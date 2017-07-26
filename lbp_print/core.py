#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LombardPress print.
"""

from hashlib import blake2b

import logging
import lxml
import os
import queue
import re
import subprocess
import threading
import urllib

import lbppy

MODULE_DIR = os.path.dirname(__file__)

class Transcription:

    def __init__(self, input, cache=None):
        self.input = input
        self.schema_info = None
        self.file = None

    def select_xlst_script(self, external=None):
        """Determine which xslt should be used.

        Return: File object
        """

        if external:
            if os.path.isfile(external):
                return open(external)
            else:
                raise IOError(f"The supplied argument ({file_argument}) is not a file.")

        if self.schema_info['type'] == 'critical':
            xslt_document_type = 'critical'
        else:
            xslt_document_type = 'diplomatic'
        xslt_version = self.schema_info['version']
        top = os.path.join(MODULE_DIR, 'xslt')
        if xslt_version in os.listdir(top):
            if xslt_document_type + '.xslt' in os.listdir(os.path.join(top, xslt_version)):
                return open(os.path.join(top, xslt_version, xslt_document_type) + '.xslt')
            else:
                raise FileNotFoundError(f"The file '{xslt_document_type}.xslt' was not found in '\
                                            {os.path.join(top, xslt_version)}.")
        else:
            raise NotADirectoryError(
                f"A directory for version {xslt_version} was not found in {top}")

    def create_hash(self):
        with open(self.xslt.name, 'br') as f:
            xslt_digest = blake2b(f.read(), digest_size=16).hexdigest()
        with open(self.file.name, 'br') as f:
            return blake2b(f.read(), digest_size=16, key=xslt_digest.encode('utf-8')).hexdigest()


class LocalTranscription(Transcription):
    """Object for handling local files."""

    def __init__(self, input):
        Transcription.__init__(self, input)
        self.file = self.define_file()
        self.schema_info = self.get_schema_info()
        self.xslt = self.select_xlst_script()
        self.digest = self.create_hash()
        logging.debug(f"Local resource initialized. {self.input}")

    def define_file(self):
        """Return the file object.
        """
        file_argument = self.input
        if os.path.isfile(file_argument):
            return open(file_argument, encoding='utf-8')
        else:
            raise IOError(f"The supplied argument ({file_argument}) is not a file.")

    def get_schema_info(self):
        """Return the validation schema version."""
        # TODO: We need validation of the xml before parsing it. This is necesssary for proper user feedback on errors.

        try:
            schemaref_number = lxml.etree.parse(self.file.name).xpath(
                "/tei:TEI/tei:teiHeader[1]/tei:encodingDesc[1]/tei:schemaRef[1]/@n",
                namespaces={"tei": "http://www.tei-c.org/ns/1.0"}
            )[0]  # The returned result is a list. Grab first element.
            return {
                'version': schemaref_number.split('-')[2],
                'type': schemaref_number.split('-')[1]
            }
        except IndexError as e:
            logging.error('The document does not seem to contain a value in '
                          'TEI/teiHeader/encodingDesc/schemaRef[@n]. See the LombardPress documentation for help. '
                          'If the problem persists, please submit an issue report.')
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

    def __init__(self, input, download_dir=False):
        Transcription.__init__(self, input)
        self.input = input
        self.download_dir = False
        self.resource = self.find_remote_resource(input)
        self.direct_transcription = False  # Does the input refer directly to a transcription.
        self.transcription_object = self.define_transcription_object()
        self.id = self.input.split('/')[-1]
        self.file = self.__define_file()
        self.schema_info = self.get_schema_info()
        self.xslt = self.select_xlst_script()
        self.digest = self.create_hash()
        logging.debug("Remote resource initialized.")
        logging.debug("Ojbect dict: {}".format(self.__dict__))

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

    def __define_file(self):
        """Determine whether the file input supplied is local or remote and return its file object.
        """
        if self.download_dir:
            download_dir = self._find_or_create_download_dir(self.download_dir)
        else:
            download_dir = self._find_or_create_download_dir('download')

        file_path = os.path.join(download_dir, self.id + '.xml')
        # We are disabling the caching temporarily until we have a better solution.
        # if os.path.isfile(file_path):
        #     logging.info(f"Using cached version of ID {self.id}.")
        #     return open(file_path)
        # else:

        logging.info("Downloading remote resource...")
        if self.direct_transcription:
            url_object = self.transcription_object.file().file().geturl()
        else:
            url_object = self.transcription_object.resource().file().file().geturl()

        with urllib.request.urlopen(url_object) as response:
            transcription_content = response.read().decode('utf-8')
            with open(file_path, mode='w', encoding='utf-8') as f:
                f.write(transcription_content)
        logging.info("Download of remote resource finished.")
        return open(f.name)

    def _find_or_create_download_dir(self, download_dir):
        if os.path.isdir(download_dir):
            return download_dir
        else:
            logging.warn(f'The supplied download directory {download_dir} does not exist. It will be created.')
            os.mkdir(download_dir)
            return download_dir


class Tex:
    """Object handling the creation and processing of the TeX representation of the item."""

    def __init__(self, transcription: Transcription, output: str = None,
                 xslt_parameters: str = None, clean_whitespace: bool =True,
                 annotate_samewords: bool =True) -> None:
        self.xml = transcription.file
        self.xslt = transcription.xslt
        self.output_dir = output
        self.xslt_parameters = xslt_parameters
        self.clean_whitespace = clean_whitespace
        self.annotate_samewords = annotate_samewords
        self.file = self.clean(self.xml_to_tex())

    def xml_to_tex(self):
        """Convert the list of encoded files to tex, using the auxiliary XSLT script.
    
        The function creates a output dir in the current working dir and puts the tex file in that
        directory. The function requires saxon installed.
    
        Keyword Arguments:
        xml_buffer -- the content of the xml file under conversion
        xslt_script -- the content of the xslt script used for the conversion
    
        Return: File object.
        """
        logging.info(f"Start conversion of {self.xml.name}...")

        if self.xslt_parameters:
            process = subprocess.Popen(['java', '-jar', os.path.join(MODULE_DIR, 'vendor/saxon9he.jar'),
                                        f'-s:{self.xml.name}', f'-xsl:{self.xslt.name}',
                                        self.xslt_parameters],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            process = subprocess.Popen(['java', '-jar', os.path.join(MODULE_DIR, 'vendor/saxon9he.jar'),
                                        f'-s:{self.xml.name}', f'-xsl:{self.xslt.name}'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = process.communicate()

        if err:
            logging.warning('The XSLT script reported the following warning(s):\n'
                            + err.decode('utf-8'))
        tex_buffer = out.decode('utf-8')

        # Output dir preparation: If output flags, check that dir and set, if not,
        # create or empty the dir "output" in current working dir.
        if self.output_dir:
            if os.path.isdir(self.output_dir):
                output_dir = self.output_dir
            else:
                logging.warning(f'The supplied output directory {self.output_dir} does not exist. '
                                f'It will be created.')
                os.mkdir(self.output_dir)
                output_dir = self.output_dir
        else:
            output_dir = 'output'
            if not output_dir in os.listdir('.'):
                os.mkdir(output_dir)
            else:
                for (root, dirs, files) in os.walk(output_dir):
                    for name in files:
                        os.remove(os.path.join(root, name))

        # Output file name based on transcription object.
        basename, _ = os.path.splitext(os.path.basename(self.xml.name))
        with open(os.path.join(output_dir, basename + '.tex'), mode='w', encoding='utf-8') as f:
            f.write(tex_buffer)
        logging.info('The XML was successfully converted.')
        return f

    def clean(self, tex_file):
        """Orchestrate cleanup of tex file.

        This is split into two subfunctions for maintainability.

        :return: File object of the text file after cleanup.
        """
        def whitespace_cleanup(self, tex_file):
            """Clean the content of the tex file for different whitespace problems.

            :return: File object of the tex file after cleanup.
            """

            logging.info("Trying to remove whitespace...")
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
                # NASTY!!!
                # quia\edtext{}{\lemma{\textnormal{quia}} => \edtext{quia}{\lemma{\textnormal{quia}}
                (r'(\w+)\\edtext{}{\\lemma{\1}', r'\\edtext{\1}{\\lemma{\1}'),

                # Replace anything wrapped in quotes ("...") with \enquote{...}. This is a bit
                # dangerous as it assumes that the editor always balances his quotes,
                # and we cannot be sure of that. The proper way to do this would be with a stack
                # tracking opening and closing quotes and alerting user on unbalanced quotes.
                # That would of course require a separate function. Would it reduce performance
                # significantly?
                (r'"([^"]+?)"', r'\\enquote{\1}'),
            ]

            # I don't like the need to go through new file. Could/should we try with a temporary
            # IO object in memory (buffer size would probably not become a real problem).
            fname = tex_file.name
            orig_fname = fname + '.orig'

            # Rename original tex file into a .tex.orig file
            try:
                os.rename(fname, orig_fname)
            except IOError:
                raise IOError("Could not create temp file for cleaning.")

            # Open original file in read only mode
            try:
                fi = open(orig_fname, mode='r', encoding='utf-8')
            except IOError:
                raise IOError("Could not open file.")

            # Create a new file that will contain the clean text
            try:
                fo = open(fname, mode='w', encoding='utf-8')
            except IOError:
                raise IOError("Could not create temp file for cleaning.")

            with fi, fo:
                for line in fi.readlines():
                    for pattern, replacement in patterns:
                        line = re.sub(pattern, replacement, line)
                    fo.write(line)

            # First check that the new file exists before deleting the old one
            if os.path.isfile(fname):
                try:
                    os.remove(orig_fname)
                except IOError:
                    logging.warning("Could not delete temp file. Continuing...")

            logging.info('Whitespace removed.')
            return fo

        if self.clean_whitespace:
            tex_file = whitespace_cleanup(self, tex_file)
        if self.annotate_samewords:
            # Not implemented yet!
            pass

        return tex_file

    def compile(self):
        """Convert a tex file to pdf with XeLaTeX.

        This requires `latexmk` and `xelatex`.

        :return: Pdf file object.
        """

        def read_output(pipe, func):
            for line in iter(pipe.readline, b''):
                func(line)
            pipe.close()

        def write_output(get):
            for line in iter(get, None):
                logging.info(line.decode('utf-8').replace('\n', ''))

        if not self.output_dir:
            output_dir = os.path.dirname(self.file.name)

        logging.info(f"Start compilation of {self.file.name}")

        process = subprocess.Popen(f'latexmk --output-directory={self.output_dir} --xelatex '
                                   f'--halt-on-error {self.file.name}',
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
            output_basename, _ = os.path.splitext(self.file.name)
            return open(output_basename + '.pdf')
        else:
            logging.error('The compilation failed. See tex output above for more info.')
            raise Exception('Latex compilation failed.')