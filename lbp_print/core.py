#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LombardPress print.
"""

from hashlib import blake2b
from tempfile import TemporaryDirectory

import json
import logging
import lxml
import os
import queue
import re
import shutil
import subprocess
import threading
import urllib

import lbppy

from lbp_print import config


class Cache:
    """Object storing and verifying data about the cache directory and registry."""

    def __init__(self, directory):
        self.dir = self.verify_dir(directory)
        self.registry_file = os.path.join(self.dir, 'registry.json') if self.dir else None
        self.registry = self.open_registry()

    def verify_dir(self, directory):
        """If a cache dir is specified, check whether it exists."""
        if directory:
            candidate = os.path.expanduser(directory)
            if os.path.isdir(candidate):
                return os.path.abspath(candidate)
            else:
                raise OSError('Specified cache directory (%s) does not exist.' % candidate)
        else:
            return None

    def open_registry(self):
        """If the cache dir is set, identify or create a registry in that dir."""
        if self.dir:
            if not os.path.isfile(self.registry_file):
                with open(self.registry_file, 'w+') as fp:
                    # Create the file, and to avoid any formatting errors, it gets a bit of content.
                    json.dump({'key': 'val'}, fp)
            with open(self.registry_file) as fp:
                return json.load(fp)

        else:
            return None

    def update_registry(self, suffixed_id, new):
        """Update the registry, remove the old version and save the updated registry file.
        """
        if self.dir:
            logging.debug('Updating cache registry.')
            if suffixed_id in self.registry:
                prev_ver = self.registry[suffixed_id]
                self.registry[suffixed_id] = new
                os.remove(os.path.join(self.dir, prev_ver))

            else:
                self.registry[suffixed_id] = new
            with open(self.registry_file, 'w') as fp:
                json.dump(self.registry, fp)

    def contains(self, basename):
        """Check whether the hash of the current transcription object is present in the cache
        directory.

        :return: Bool
        """
        if self.dir:
            location = os.path.join(self.dir, basename)
            if os.path.isfile(location):
                return True
            else:
                return False

    def store(self, src, dst_digest, src_id, suffix):
        """Store result in cache dir when applicaple. Remove earlier version of id if present.

        :return: String of cache file or None if no cache dir."""
        if self.dir:
            logging.debug('Storing {} in cache dir ({})'.format(src.name, self.dir))
            try:
                self.update_registry(src_id + suffix, dst_digest + suffix)
                return shutil.copyfile(src.name, os.path.join(self.dir, dst_digest + suffix))
            except:
                raise
        else:
            logging.debug('Cache dir is not set.')
            return None


class Transcription:

    def __init__(self, input):
        self.input = input
        self.schema_info = None
        self.file = None
        self.tmp_dir = TemporaryDirectory()

    def select_xlst_script(self, external=None):
        """Determine which xslt should be used.

        Return: File object
        """

        if external:
            if os.path.isfile(external):
                return open(external).name
            else:
                raise IOError(f"The supplied argument ({file_argument}) is not a file.")

        if self.schema_info['type'] == 'critical':
            xslt_document_type = 'critical'
        else:
            xslt_document_type = 'diplomatic'
        xslt_ver = self.schema_info['version']
        top = os.path.join(config.module_dir, 'xslt')
        if xslt_ver in os.listdir(top):
            if xslt_document_type + '.xslt' in os.listdir(os.path.join(top, xslt_ver)):
                return os.path.abspath(os.path.join(top, xslt_ver, xslt_document_type) + '.xslt')
            else:
                raise FileNotFoundError(f"The file '{xslt_document_type}.xslt' was not found in '\
                                            {os.path.join(top, xslt_ver)}.")
        else:
            raise NotADirectoryError(
                f"A directory for version {xslt_ver} was not found in {top}")

    def create_hash(self):
        with open(self.xslt, 'br') as f:
            xslt_digest = blake2b(f.read(), digest_size=16).hexdigest()
        with open(self.file, 'br') as f:
            return blake2b(f.read(), digest_size=16, key=xslt_digest.encode('utf-8')).hexdigest()


class LocalTranscription(Transcription):
    """Object for handling local files."""

    def __init__(self, input, custom_xslt=None):
        Transcription.__init__(self, input)
        self.file = self.copy_to_file()
        self.id = os.path.splitext(os.path.basename(self.input))[0]
        self.schema_info = self.get_schema_info()
        self.xslt = self.select_xlst_script(external=custom_xslt)
        self.digest = self.create_hash()
        logging.debug(f"Local resource initialized. {self.input}")
        logging.debug("Object dict: {}".format(self.__dict__))

    def copy_to_file(self):
        """Copy the input file to a temporary file object that we can delete later.

        :return: File object.
        """
        file_argument = os.path.expanduser(self.input)
        if os.path.isfile(file_argument):
            shutil.copy(file_argument, self.tmp_dir.name)
            return os.path.join(self.tmp_dir.name, os.path.basename(file_argument))
        else:
            raise IOError(f"The supplied argument ({file_argument}) is not a file.")

    def get_schema_info(self):
        """Return the validation schema version."""
        # TODO: We need validation of the xml before parsing it. This is necesssary for proper user
        # feedback on errors.

        try:
            schemaref_number = lxml.etree.parse(self.file).xpath(
                "/tei:TEI/tei:teiHeader[1]/tei:encodingDesc[1]/tei:schemaRef[1]/@n",
                namespaces={"tei": "http://www.tei-c.org/ns/1.0"}
            )[0]  # The returned result is a list. Grab first element.
            return {
                'version': schemaref_number.split('-')[2],
                'type': schemaref_number.split('-')[1]
            }
        except IndexError as e:
            logging.error('The document does not seem to contain a value in '
                          'TEI/teiHeader/encodingDesc/schemaRef[@n]. See the LombardPress '
                          'documentation for help. If the problem persists, please submit an issue '
                          'report.')
            raise
        except Exception as e:
            logging.error('The process resulted in an error: {}.\n '
                          'If the problem persists, please submit an issue report.'.format(e))
            raise


class RemoteTranscription(Transcription):
    """Object for handling remote transcriptions.

    Keyword arguments:
    input -- SCTA resource id of the text to be processed.
    """

    def __init__(self, input, custom_xslt=None):
        Transcription.__init__(self, input)
        self.input = input
        self.download_dir = False
        self.resource = self.find_remote_resource(input)
        self.direct_transcription = False  # Does the input refer directly to a transcription.
        self.transcription_object = self.define_transcription_object()
        self.id = self.input.split('/')[-1]
        self.file = self.download_to_file()
        self.schema_info = self.get_schema_info()
        self.xslt = self.select_xlst_script(external=custom_xslt)
        self.digest = self.create_hash()
        logging.debug("Remote resource initialized.")
        logging.debug("Object dict: {}".format(self.__dict__))

    def get_schema_info(self):
        """Return the validation schema version."""
        if self.direct_transcription:
            return {
                'version': self.transcription_object.file().validating_schema_version(),
                'type': self.transcription_object.transcription_type()
            }
        else:
            return {
                'version': self.transcription_object.resource().file().validating_schema_version(),
                'type': self.transcription_object.resource().transcription_type()
            }

    def find_remote_resource(self, resource_input):

        url_match = re.match(r'(http://)?(scta.info/resource)?', resource_input)
        url_string = ''
        if url_match:
            if url_match.group(1) is None:
                url_string += 'http://'
            if not url_match.group(2):
                url_string += 'scta.info/resource/'

        url_string += resource_input
        try:
            return lbppy.Resource.find(url_string)
        except AttributeError:
            logging.error(f'A resource with the provided ID ("{url_string}") could not be located. '
                          'Ensure that you have entered the correct id. ')
            raise

    def define_transcription_object(self):
        """
        Return a canonical transcription of either Manifestation (critical) or Expression (
        diplomatic) objects.
        """
        if isinstance(self.resource, lbppy.Expression):
            return self.resource.canonical_manifestation().resource().canonical_transcription()
        elif isinstance(self.resource, lbppy.Manifestation):
            return self.resource.canonical_transcription()
        elif isinstance(self.resource, lbppy.Transcription):
            self.direct_transcription = True
            return self.resource

    def download_to_file(self):
        """Download the remote object and store in a temporary file.

        :return: File object
        """
        tmp_file = open(os.path.join(self.tmp_dir.name, 'tmp'), mode='w')

        logging.info("Downloading remote resource...")
        if self.direct_transcription:
            url_object = self.transcription_object.file().file().geturl()
        else:
            url_object = self.transcription_object.resource().file().file().geturl()

        with urllib.request.urlopen(url_object) as response:
            transcription_content = response.read().decode('utf-8')
            with open(tmp_file.name, mode='w', encoding='utf-8') as f:
                f.write(transcription_content)
        logging.info("Download of remote resource finished.")
        return f.name


class Tex:
    """Object handling the creation and processing of the TeX representation of the item."""

    def __init__(self, transcription: Transcription, output_format: str = None,
                 output_dir: str = None, xslt_parameters: str = None, clean_whitespace: bool = True,
                 annotate_samewords: bool = True) -> None:
        self.id = transcription.id
        self.xml = transcription.file
        self.xslt = transcription.xslt
        self.digest = transcription.digest
        self.tmp_dir = transcription.tmp_dir
        self.output_format = output_format
        self.output_dir = output_dir
        self.cache = Cache(config.cache_dir)
        self.xslt_parameters = xslt_parameters
        self.clean_whitespace = clean_whitespace
        self.annotate_samewords = annotate_samewords

    def process(self):
        """Convert an XML file to TeX and compile it to PDF with XeLaTeX if required.

        Depending on the requested output format, this returns either a TeX file or a PDF file
        object.

        :return: File object.
        """

        def store_output(src, dst_basename):
            """Store result in output dir when applicaple."""
            if self.output_dir:
                logging.debug('Output dir is set to %s' % self.output_dir)
                try:
                    return shutil.copyfile(src.name, os.path.join(self.output_dir, dst_basename))
                except:
                    raise
            else:
                logging.debug('Output dir is not set.')

            return src.name

        output_file = self.clean(self.xml_to_tex())

        if self.output_format == 'pdf':
            output_file = self.compile(output_file)
            output_suffix = '.pdf'
        else:
            output_suffix = '.tex'

        # All done, now we remove the temporary directory before returning the output file.
        result_dir = store_output(output_file, self.id + output_suffix)
        self.tmp_dir.cleanup()
        return result_dir

    def xml_to_tex(self):
        """Convert the list of encoded files to tex, using the auxiliary XSLT script.
    
        The function creates a output dir in the current working dir and puts the tex file in that
        directory. The function requires saxon installed.
    
        Keyword Arguments:
        xml_buffer -- the content of the xml file under conversion
        xslt_script -- the content of the xslt script used for the conversion
    
        Return: File object.
        """

        if self.cache.contains(basename=self.digest + '.tex'):
            logging.info(f"Using cached version of {self.id}.")
            return open(os.path.join(self.cache.dir, self.digest + '.tex'))
        else:
            logging.info(f"Start conversion of {self.id}.")
            logging.debug(f"Using XSLT: {self.xslt}.")

            if self.xslt_parameters:
                process = subprocess.Popen(['java', '-jar',
                                            os.path.join(config.module_dir, 'vendor/saxon9he.jar'),
                                            f'-s:{self.xml}', f'-xsl:{self.xslt}',
                                            self.xslt_parameters],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                process = subprocess.Popen(['java', '-jar',
                                            os.path.join(config.module_dir, 'vendor/saxon9he.jar'),
                                            f'-s:{self.xml}', f'-xsl:{self.xslt}'],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()

            if err:
                logging.warning('The XSLT script reported the following warning(s):\n'
                                + err.decode('utf-8'))
            tex_buffer = out.decode('utf-8')

            # Output file name based on transcription object.
            temp_location = os.path.join(self.tmp_dir.name, self.digest + '.tex')
            with open(temp_location, mode='w+', encoding='utf-8') as f:
                f.write(tex_buffer)
            logging.info('The XML was successfully converted.')

            self.cache.store(f, dst_digest=self.digest, src_id=self.id, suffix='.tex')

            return f

    def whitespace_cleanup(self, tex_file):
        """Clean the content of the tex file for different whitespace problems.

        :return: File object of the tex file after cleanup.
        """

        logging.debug("Trying to remove whitespace...")
        patterns = [
            (r' ?{ ?', r'{'),  # Remove redundant space around opening bracket.
            (r' }', r'}'),  # Remove redundant space before closing bracket.
            (r' ([.,?!:;])', r'\1'),  # Remove redundant space before punctuation.
            (r' (\\edtext{})', r'\1'),  # Remove space before empty lemma app notes.
            (r'}(\\edtext{[^}]})', r'} \1'),  # Add missing space between adjacent app. notes.
            (r' +', ' '),  # Remove excessive whitespace.
            (r'} ([.,?!:;])', r'}\1'),
            # Remove redundant space between closing brackets. and punctuation.
            (r'^ +', r''),  # Remove leading space at beginning of line.
            (r' %$', '%'),  # Remove trailing whitespace at paragraph end.
            ('\( ', r'('),  # Remove trailing whitespace inside parenthesis.
            ('([_\^])', r'\\\1'),  # Escape _ and ^ characters.

            # Replace anything wrapped in quotes ("...") with \enquote{...}. This is a bit
            # dangerous as it assumes that the editor always balances his quotes,
            # and we cannot be sure of that. The proper way to do this would be with a stack
            # tracking opening and closing quotes and alerting user on unbalanced quotes.
            # That would of course require a separate function. Would it reduce performance
            # significantly?
            (r'"([^"]+?)"', r'\\enquote{\1}'),
        ]

        with open(tex_file.name) as f:
            buffer = f.read()

        for pattern, replacement in patterns:
            buffer = re.sub(pattern, replacement, buffer, flags=re.MULTILINE)

        with open(tex_file.name, 'w') as f:
            f.write(buffer)

        logging.debug('Whitespace removed.')
        return tex_file

    def clean(self, tex_file):
        """Orchestrate cleanup of tex file.

        This is split into two subfunctions for maintainability.

        :return: File object of the text file after cleanup.
        """

        if self.clean_whitespace:
            tex_file = self.whitespace_cleanup(tex_file)
        if self.annotate_samewords:
            # Not implemented yet!
            pass
        return tex_file

    def compile(self, input_file):
        """Convert a tex file to pdf with XeLaTeX.

        This requires `latexmk` and `xelatex`.

        :return: Pdf file object.
        """
        def clean_tex_dir(directory):
            for file in os.listdir(directory):
                if os.path.splitext(file)[1] not in ['.pdf', '.tex']:
                    os.remove(os.path.join(directory, file))

        def read_output(pipe, func):
            for line in iter(pipe.readline, b''):
                func(line)
            pipe.close()

        def write_output(get):
            for line in iter(get, None):
                logging.info(line.decode('utf-8').replace('\n', ''))

        if self.cache.contains(self.digest + '.pdf'):
            logging.debug('Using cached pdf.')
            return open(os.path.join(self.cache.dir, self.digest + '.pdf'))

        else:
            logging.info(f"Start compilation of {self.id}")
            process = subprocess.Popen(
                f'latexmk --xelatex --output-directory={self.tmp_dir.name} '
                f'--halt-on-error '
                f'{re.escape(input_file.name)}',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, bufsize=1)
            q = queue.Queue()
            out_thread = threading.Thread(target=read_output, args=(process.stdout, q.put))
            err_thread = threading.Thread(target=read_output, args=(process.stderr, q.put))
            write_thread = threading.Thread(target=write_output, args=(q.get,))

            for t in (out_thread, err_thread, write_thread):
                t.start()

            process.wait()
            q.put(None)

            if process.returncode == 0:
                # Process finished. We clean the tex dir and return the file object from that dir.
                output_file = open(
                    os.path.join(
                        self.tmp_dir.name,
                        os.path.splitext(os.path.basename(input_file.name))[0])
                    + '.pdf'
                )
                self.cache.store(output_file, dst_digest=self.digest, src_id=self.id, suffix='.pdf')
                return output_file
            else:
                logging.error('The compilation failed. See tex output above for more info.')
                raise Exception('Latex compilation failed.')
