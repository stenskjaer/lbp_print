#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LombardPress print.

Usage:
  lbp_print (tex|pdf) [options] --local <file>...
  lbp_print (tex|pdf) [options] --scta <expression-id>...
  lbp_print recipe <recipe> [options]

Pull LBP-compliant files from SCTA repositories or use local, convert them into
tex or pdf.

Arguments:
  <file>                   Location of one or more local files to be processed.
  <expression-id>          The expression id of the items to be processed.

Multiple arguments are separated with whitespace.

Commands:
  tex                      Convert the xml to a tex-file.
  pdf                      Convert the xml to a tex-file and compile it into a
                           pdf.
  recipe <recipe>          Follow recipe in config file at <file> location.

Options:
  --scta                   Flag. When present, the <identifier> should be an
                           expression id of the SCTA database.
  --local                  Flag. When present, process local file indicated
                           by <file> argument.
  --xslt <file>            Use a custom xslt file in place of the default
                           supplied templates.
  --output, -o <dir>       Put results in the specified directory.
  --xslt-parameters <str>  Command line parameters that will be
                           passed to the XSLT script. Unfortunately, this only
                           works with one parameter at the moment.
                           Example: --xslt-parameters "key=value"
  --config-file <file>     Location of a config file in json format.
                           [default: ~/.lbp_print.json]
  -V, --verbosity <level>  Set verbosity. Possibilities: silent, info, debug
                           [default: info].
  -v, --version            Show version and exit.
  -h, --help               Show this help message and exit.
"""

import logging
import os

from docopt import docopt

from lbp_print.core import LocalTranscription, RemoteTranscription, select_xlst_script, clean_tex, \
    convert_xml_to_tex, compile_tex
from lbp_print.__about__ import __version__

def load_config(filename):
    """Load and read in configuration from local config file.

    :return Dictionary of the configuration."""
    import json

    try:
        with open(filename, mode='r') as f:
            try:
                conf = json.loads(f.read())
            except json.decoder.JSONDecodeError as e:
                logging.error(f"The config file {f.name} is incorrectly formatted.\n"
                              f"JSON deconding gave the following error: {e}")
                raise

            # Expand user commands in file arguments.
            print(conf)
            if '<file>' in conf:
                conf['<file>'] = [os.path.expanduser(item) for item in conf['<file>']]
            if '--output' in conf:
                conf['--output'] = os.path.expanduser(conf['--output'])

            return conf
    except:
        logging.warning(f'The config file {filename} was not found. Default settings will be used.')
        return {}

def merge(dict_1, dict_2):
    """Merge two dictionaries.
    Values that evaluate to true take priority over falsy values.
    `dict_1` takes priority over `dict_2`.
    """
    return dict((str(key), dict_1.get(key) or dict_2.get(key))
                for key in set(dict_2) | set(dict_1))

def main():

    logging.basicConfig(level='INFO', format="%(levelname)s: %(message)s")

    # Read command line arguments
    cl_args = docopt(__doc__, version=__version__)

    # Expand user dir for config file.
    cl_args['--config-file'] = os.path.expanduser(cl_args['--config-file'])

    # Read config file or recipe
    if cl_args['<recipe>']:
        ini_args = load_config(cl_args['<recipe>'])
    else:
        ini_args = load_config(cl_args['--config-file'])

    # Merge configurations, giving command line arguments priority over config file arguments
    args = merge(cl_args, ini_args)

    # Setup logging according to configuration
    logging.getLogger().setLevel(args['--verbosity'].upper())

    # Debug startup info
    logging.debug('Logging initialized.')
    logging.debug(args)
    logging.debug('App initialized.')

    # Determine output directory
    if args["--output"]:
        output_dir = args["--output"]
    else:
        output_dir = False

    # Initialize the object
    transcriptions = []
    if args["--scta"]:
        for num, exp in enumerate(args["<expression-id>"], 1):
            logging.info(f'Initializing {exp}. [{num}/{len(args["<expression-id>"])}]')
            transcriptions.append(RemoteTranscription(exp))
    elif args["--local"]:
        for num, exp in enumerate(args["<file>"], 1):
            logging.info(f'Initializing {exp}. [{num}/{len(args["<file>"])}]')
            transcriptions.append(LocalTranscription(exp))
    else:
        raise ValueError("Either provide an expression-id or a reference to a local file.")

    for num, item in enumerate(transcriptions, 1):
        # Determine xslt script file (either provided or selected based on the xml transcription)
        logging.info('-------')
        logging.info(f'Processing {item.input}. [{num}/{len(transcriptions)}]')
        if args["--xslt"]:
            xslt_candidate = args["--xslt"]
            if os.path.isfile(xslt_candidate):
                xslt_script = xslt_candidate
            else:
                raise FileNotFoundError(f"The xslt file supplied, {xslt_candidate}, was not found.")
        else:
            xslt_script = select_xlst_script(item)

        tex_file = convert_xml_to_tex(item.file.name, xslt_script, output_dir, args["--xslt-parameters"])

        # clean tex file
        # there could be an option for whether or not a person wants this white space cleaning to take effect
        output_file = clean_tex(tex_file)

        if args["pdf"]:
            output_file = compile_tex(tex_file, output_dir)

        logging.info('Results returned sucessfully.\n '
                     'The output file is located at %s' % output_file.name)
