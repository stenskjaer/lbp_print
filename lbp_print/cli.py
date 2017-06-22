#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LombardPress print.

Usage:
  lbp_print (tex|pdf) [options] --local <file>...
  lbp_print (tex|pdf) [options] --scta <expression-id>...

Pull LBP-compliant files from SCTA repositories or use local, convert them into
tex or pdf.

Arguments:
  <file>                   Location of (local) file to be processed.
  <expression-id>          The expression id of the item to be processed.

Commands:
  tex                      Convert the xml to a tex-file.
  pdf                      Convert the xml to a tex-file and compile it into a
                           pdf.

Options:
  --scta                   Boolean. When True, the <identifier> should be an
                           expression id of the SCTA database.
  --local                  Boolean. Process local file.
  --xslt <file>            Use a custom xslt file in place of the default
                           supplied templates.
  --output, -o <dir>       Put results in the specified directory.
  --xslt-parameters <str>  Command line parameters that will be
                           passed to the XSLT script. Unfortunately, this only
                           works with one parameter at the moment.
                           Example: --xslt-params "key=value"
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


def main():

    # Read command line arguments
    args = docopt(__doc__, version=__version__)

    # Setup logging
    log_formatter = logging.Formatter()
    verbosity = args['--verbosity']
    logging.basicConfig(level=verbosity.upper(), format="%(levelname)s: %(message)s")
    logging.debug(args)

    logging.debug('App initialized.')
    logging.debug('Logging initialized.')

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
