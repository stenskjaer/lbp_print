#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LombardPress print.
"""

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
    """The main object of the script, defining the properties of the text under processing."""

    def __init__(self, input_argument):
        self.input = input_argument

    def get_schema_info(self):
        """Return schema version info."""
        pass

    def _define_file(self):
        """Return file object.
        """
        pass


class LocalTranscription(Transcription):
    """Object for handling local files."""

    def __init__(self, input):

        Transcription.__init__(self, input)
        self.file = self._define_file()
        self.lbp_schema_info = self.get_schema_info()

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


    def _define_file(self):
        """Return the file object.
        """
        file_argument = self.input
        if os.path.isfile(file_argument):
            return open(file_argument)
        else:
            raise IOError(f"The supplied argument ({file_argument}) is not a file.")


class RemoteTranscription(Transcription):
    """Object for handling remote transcriptions.

    Keyword arguments:
    input -- SCTA resource id of the text to be processed.
    """

    def __init__(self, resource_input, download_dir=False):
        Transcription.__init__(self, resource_input)
        self.download_dir = download_dir
        self.resource = self.find_remote_resource(resource_input)
        try:
            self.transcription_object = self.define_transcription_object()
        except:
            logging.info(f'No critical transcription for {resource_input}, use first available transcription.')
            self.transcription_object = self.resource.manifestations()[0].resource().canonical_transcription()
        self.id = self.input.split('/')[-1]
        self.file = self._define_file()
        self.lbp_schema_info = self.get_schema_info()

    def get_schema_info(self):
        """Return the validation schema version."""
        return {
            'version': self.transcription_object.resource().file().validating_schema_version(),
            'type': self.transcription_object.resource().transcription_type()
        }

    def find_remote_resource(self, resource_input):
        try:
            return lbppy.Resource.find(resource_input)
        except AttributeError:
            logging.error(f'A resource with the provided ID ("{resource_input}") could not be located. '
                          'Ensure that you have entered the correct id. ')
            raise

    def define_transcription_object(self):
        if isinstance(self.resource, lbppy.Expression):
            return self.resource.canonical_manifestation().resource().canonical_transcription()
        elif isinstance(self.resource, lbppy.Manifestation):
            return self.resource.canonical_transcription()

    def _define_file(self):
        """Determine whether the file input supplied is local or remote and return its file object.
        """
        logging.info("Remote resource initialized.")
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
        with urllib.request.urlopen(self.transcription_object.resource().file().file().geturl()) as response:
            transcription_content = response.read().decode('utf-8')
            with open(file_path, mode='w') as f:
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


def convert_xml_to_tex(xml_file, xslt_script, output=False, xslt_parameters=False):
    """Convert the list of encoded files to tex, using the auxiliary XSLT script.

    The function creates a output dir in the current working dir and puts the tex file in that
    directory. The function requires saxon installed.

    Keyword Arguments:
    xml_buffer -- the content of the xml file under conversion
    xslt_script -- the content of the xslt script used for the conversion

    Return: File object.
    """
    logging.info(f"Start conversion of {xml_file}...")

    if xslt_parameters:
        process = subprocess.Popen(['java', '-jar', os.path.join(MODULE_DIR, 'vendor/saxon9he.jar'),
                                    f'-s:{xml_file}', f'-xsl:{xslt_script}', xslt_parameters],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(['java', '-jar', os.path.join(MODULE_DIR, 'vendor/saxon9he.jar'),
                                    f'-s:{xml_file}', f'-xsl:{xslt_script}'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = process.communicate()

    if err:
        logging.warning('The XSLT script reported the following warning(s):\n'
                        + err.decode('utf-8'))
    tex_buffer = out.decode('utf-8')

    # Output dir preparation: If output flags, check that dir and set, if not,
    # create or empty the dir "output" in current working dir.
    if output:
        if os.path.isdir(output):
            output_dir = output
        else:
            logging.warn(f'The supplied output directory {output} does not exist. It will be created.')
            os.mkdir(output)
            output_dir = output
    else:
        output_dir = 'output'
        if not output_dir in os.listdir('.'):
            os.mkdir(output_dir)
        else:
            for (root, dirs, files) in os.walk(output_dir):
                for name in files:
                    os.remove(os.path.join(root, name))

    # Output file name based on transcription object.
    basename, _ = os.path.splitext(os.path.basename(xml_file))
    with open(os.path.join(output_dir, basename + '.tex'), mode='w', encoding='utf-8') as f:
        f.write(tex_buffer)
    logging.info('The XML was successfully converted.')
    return f


def clean_tex(tex_file):
    """Clean the content of the tex file for different whitespace problems.

    Side effect: This changes the content of the file.

    :param tex_file: File object of the tex file.
    :return: File object of the tex file after cleanup.
    """
    logging.info("Trying to remove whitespace...")
    patterns = [
        (r' ?{ ?', r'{'),                 # Remove redundant space around opening bracket.
        (r' }', r'}'),                    # Remove redundant space before closing bracket.
        (r' ([.,?!:;])', r'\1'),          # Remove redundant space before punctuation.
        (r' (\\edtext{})', r'\1'),        # Remove space before empty lemma app notes.
        (r'}(\\edtext{[^}]})', r'} \1'),  # Add missing space between adjacent app. notes.
        (r' +', ' '),                     # Remove excessive whitespace.
        (r'} ([.,?!:;])', r'}\1'),        # Remove redundant space between closing brackets. and punctuation.
        (r'^ +', r''),                    # Remove leading space at beginning of line.
        (r' %$', '%'),                    # Remove trailing whitespace at paragraph end.

        # Replace anything wrapped in "..." with \enquote{...}. This is a bit dangerous as it
        # assumes that the editor always balances his quotes, and we cannot be sure of that.
        (r'"([^"]+?)"', r'\\enquote{\1}'),
    ]
    fname = tex_file.name
    orig_fname = fname + '.orig'

    # Rename original tex file into a .tex.orig file
    try:
        os.rename(fname, orig_fname)
    except IOError:
        raise IOError("Could not create temp file for cleaning.")

    # Open original file in read only mode
    try:
        fi = open(orig_fname, 'r')
    except IOError:
        raise IOError("Could not open file.")

    # Create a new file that will contain the clean text
    try:
        fo = open(fname, 'w')
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


def compile_tex(tex_file, output_dir=False):
    """Convert a tex file to pdf with XeLaTeX.

    This requires `latexmk` and `xelatex`.

    Keyword Arguments:
    tex_file -- the tex file object to be converted.
    output_dir -- the directory where latexmk should put the created files. [default: tex file dir]

    Return: Output file object.
    """

    def read_output(pipe, func):
        for line in iter(pipe.readline, b''):
            func(line)
        pipe.close()

    def write_output(get):
        for line in iter(get, None):
            logging.info(line.decode('utf-8').replace('\n', ''))

    if not output_dir:
        output_dir = os.path.dirname(tex_file.name)

    logging.info(f"Start compilation of {tex_file.name}")

    process = subprocess.Popen(f'latexmk --output-directory={output_dir} --xelatex '
                               f'--halt-on-error {tex_file.name}',
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
        output_basename, _ = os.path.splitext(tex_file.name)
        return open(output_basename + '.pdf')
    else:
        logging.error('The compilation failed. See tex output above for mor info.')
        raise Exception('Latex compilation failed.')


def select_xlst_script(trans_obj):
    """Determine which xslt should be used.

    If a URL is provided, the script is downloaded and stored temporarily. If a local file is
    provided, its location is used.

    Keyword Arguments:
    -- trans_obj: Required. The object of the text under processing.
    -- url: The url of an external script.
    -- local: The location of a local script.

    Return: Directory as string.
    """
    schema_info = trans_obj.lbp_schema_info
    if schema_info['type'] == 'critical':
        xslt_document_type = 'critical'
    else:
        xslt_document_type = 'diplomatic'
    xslt_version = schema_info['version']
    top = os.path.join(MODULE_DIR, 'xslt')
    if xslt_version in os.listdir(top):
        if xslt_document_type + '.xslt' in os.listdir(os.path.join(top, xslt_version)):
            return os.path.relpath(os.path.join(top, xslt_version, xslt_document_type)) + '.xslt'
        else:
            raise FileNotFoundError(f"The file '{xslt_document_type}.xslt' was not found in '\
                                    {os.path.join(top, xslt_version)}.")
    else:
        raise NotADirectoryError(f"A directory for version {xslt_version} was not found in {top}")


