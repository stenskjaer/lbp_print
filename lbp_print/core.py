#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LombardPress print.
"""

from hashlib import blake2b
from tempfile import TemporaryDirectory
from typing import Union, List

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
import samewords

from lbp_print import config

# Setup logging according to configuration
logging.basicConfig(format="%(levelname)s: %(message)s")
logging.getLogger().setLevel(config.log_level)


class Cache:
    """Object storing and verifying data about the cache directory and registry."""

    def __init__(self, directory):
        self.dir = self.verify_dir(directory)
        self.registry_file = (
            os.path.join(self.dir, "registry.json") if self.dir else None
        )

    def verify_dir(self, directory):
        """If a cache dir is specified, check whether it exists."""
        if directory:
            candidate = os.path.expanduser(directory)
            if not os.path.isdir(candidate):
                logging.warning(
                    f"Specified cache directory ({candidate}) does not exist. "
                    "It will be created now."
                )
                os.mkdir(candidate)
            return os.path.abspath(candidate)
        else:
            raise Exception("Cache dir is not configured.")

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

    def store(self, filename, digest: str, suffix: str) -> str:
        """Store result in cache dir and remove earlier version of resource id.

        :return: String of cache file or None if no cache dir."""
        logging.debug(f"Storing {filename} in cache dir ({self.dir})")
        return shutil.copyfile(filename, os.path.join(self.dir, digest + suffix))


class Resource:
    def __init__(self, input):
        self.input = input
        self.schema_info = {}
        self.file = None
        self.tmp_dir = TemporaryDirectory()

    def select_xlst_script(self, schema_info={}, external=None) -> str:
        """Determine which xslt should be used.

        Return: File object
        """
        if external:
            try:
                return open(external).name
            except:
                raise

        if schema_info == None and external == None:
            raise AttributeError(
                f"The file {self.input} does not have "
                f"a correct "
                f"`/teiHeader/encodingDesc/schemaRef` "
                f"element (see LombardPress documentation), "
                f"and no custom xslt is provided, so the "
                f"correct xslt script cannot be determined."
            )
        try:
            if schema_info["type"] == "critical":
                xslt_document_type = "critical"
            elif schema_info["type"] == "critical":
                xslt_document_type = "diplomatic"
        except KeyError:
            raise AttributeError(
                "The property `schema_info@type` must be "
                "either `critical` or `diplomatic`."
            )
        xslt_ver = schema_info.get("version")
        top = os.path.join(config.module_dir, "xslt")
        if xslt_ver in os.listdir(top):
            if xslt_document_type + ".xslt" in os.listdir(os.path.join(top, xslt_ver)):
                return os.path.abspath(
                    os.path.join(top, xslt_ver, xslt_document_type) + ".xslt"
                )
            else:
                raise FileNotFoundError(
                    f"The file '{xslt_document_type}.xslt' was not found in '\
                                            {os.path.join(top, xslt_ver)}."
                )
        else:
            raise NotADirectoryError(
                f"A directory for version {xslt_ver} was not found in {top}"
            )

    def get_schema_info(self):
        """Return the validation schema version."""
        # TODO: We need validation of the xml before parsing it. This is necesssary for proper user
        # feedback on errors.

        try:
            schemaref_number = lxml.etree.parse(self.file).xpath(
                "/tei:TEI/tei:teiHeader[1]/tei:encodingDesc[1]/tei:schemaRef[1]/@n",
                namespaces={"tei": "http://www.tei-c.org/ns/1.0"},
            )[
                0
            ]  # The returned result is a list. Grab first element.
            return {
                "version": schemaref_number.split("-")[2],
                "type": schemaref_number.split("-")[1],
            }
        except IndexError as e:
            logging.warning(
                "The document does not seem to contain a value in "
                "TEI/teiHeader/encodingDesc/schemaRef[@n]. See "
                "the LombardPress documentation for help. This "
                "means that an appropriate XSLT script cannot "
                "automatically be determined. This is a problem "
                "if no custom xslt script is provided."
            )
            return None
        except Exception as e:
            logging.error(
                "The process resulted in an error: {}.\n "
                "If the problem persists, please submit an issue "
                "report.".format(e)
            )
            raise

    def create_hash(self):
        try:
            with open(self.xslt, "br") as f:
                xslt_digest = blake2b(f.read(), digest_size=16).hexdigest()
            with open(self.file, "br") as f:
                return blake2b(
                    f.read(), digest_size=16, key=xslt_digest.encode("utf-8")
                ).hexdigest()
        except:
            raise


class UrlResource(Resource):
    """Object for handling resources with a URL address."""

    def __init__(self, url, custom_xslt=None):
        super().__init__(url)
        self.file = self._download_to_file(url)
        self.xslt = self.select_xlst_script(
            schema_info=self.get_schema_info(), external=custom_xslt
        )
        self.digest = self.create_hash()
        self.id = self.digest
        logging.debug(f"Url resource initialized with url: {url}")
        logging.debug("Object dict: {}".format(self.__dict__))

    def _download_to_file(self, url) -> str:
        """Download the remote object and store in a temporary file.
        """
        tmp_file = open(os.path.join(self.tmp_dir.name, "download"), mode="w")

        logging.info("Downloading remote resource...")
        with urllib.request.urlopen(url) as response:
            transcription_content = response.read().decode("utf-8")
            with open(tmp_file.name, mode="w", encoding="utf-8") as f:
                f.write(transcription_content)
        logging.info("Download of remote resource finished.")
        return f.name


class LocalResource(Resource):
    """Object for handling local files."""

    def __init__(self, filename, custom_xslt=None):
        super().__init__(filename)
        self.file = filename
        self.xslt = self.select_xlst_script(
            schema_info=self.get_schema_info(), external=custom_xslt
        )
        self.digest = self.create_hash()
        self.id = self.digest
        self.file = self.copy_to_temp_dir(filename)
        logging.debug(f"Local resource initialized. {filename}")
        logging.debug("Object dict: {}".format(self.__dict__))

    def copy_to_temp_dir(self, filename):
        """Copy the input file to a temporary file object that we can delete later.

        :return: File object.
        """
        source = os.path.expanduser(filename)
        destination = os.path.join(self.tmp_dir.name, self.digest + ".tex")
        if os.path.isfile(source):
            shutil.copyfile(source, destination)
            return destination
        else:
            raise IOError(f"The supplied argument ({source}) is not a file.")


class RemoteResource(Resource):
    """Object for handling remote transcriptions.

    Keyword arguments:
    input -- SCTA resource id of the text to be processed.
    """

    def __init__(self, input_id, custom_xslt=None):
        super().__init__(input_id)
        transcription = self._define_transcription_object(
            self._find_remote_resource(input_id)
        )
        self.file = self._download_to_file(transcription)
        self.xslt = self.select_xlst_script(
            schema_info=self._get_schema_info(transcription), external=custom_xslt
        )
        self.digest = self.create_hash()
        self.id = self.digest
        logging.debug("Remote resource initialized.")
        logging.debug("Object dict: {}".format(self.__dict__))

    def _is_direct_transcription(self, transcription_obj):
        return isinstance(transcription_obj, lbppy.Transcription)

    def _get_schema_info(self, transcription_object):
        """Return the validation schema version."""
        logging.info("Getting information about the transcription schema.")
        if self._is_direct_transcription(transcription_object):
            return {
                "version": transcription_object.file().validating_schema_version(),
                "type": transcription_object.transcription_type(),
            }
        else:
            return {
                "version": transcription_object.resource()
                .file()
                .validating_schema_version(),
                "type": transcription_object.resource().transcription_type(),
            }

    def _find_remote_resource(self, resource_input):

        url_match = re.match(r"(http://)?(scta.info/resource)?", resource_input)
        url_string = ""
        if url_match:
            if url_match.group(1) is None:
                url_string += "http://"
            if not url_match.group(2):
                url_string += "scta.info/resource/"

        url_string += resource_input
        try:
            return lbppy.Resource.find(url_string)
        except AttributeError:
            logging.error(
                f'A resource with the provided ID ("{url_string}") could not be located. '
                "Ensure that you have entered the correct id. "
            )
            raise
        except urllib.error.URLError as exc:
            logging.error(f"Unable to connect to the resource. Error message: {exc}")
            raise

    def _define_transcription_object(self, resource):
        """
        Return a canonical transcription of either Manifestation (critical) or Expression (
        diplomatic) objects.
        """
        if isinstance(resource, lbppy.Expression):
            return (
                resource.canonical_manifestation().resource().canonical_transcription()
            )
        elif isinstance(resource, lbppy.Manifestation):
            return resource.canonical_transcription()
        elif isinstance(resource, lbppy.Transcription):
            return resource

    def _download_to_file(self, transcription_obj):
        """Download the remote object and store in a temporary file.

        :return: File object
        """
        tmp_file = open(os.path.join(self.tmp_dir.name, "tmp"), mode="w")

        logging.info("Downloading remote resource...")
        if self._is_direct_transcription(transcription_obj):
            url_object = transcription_obj.file().file().geturl()
        else:
            url_object = transcription_obj.resource().file().file().geturl()

        with urllib.request.urlopen(url_object) as response:
            transcription_content = response.read().decode("utf-8")
            with open(tmp_file.name, mode="w", encoding="utf-8") as f:
                f.write(transcription_content)
        logging.info("Download of remote resource finished.")
        return f.name


class SaxonRecord:
    def __init__(self, content) -> None:
        self.content = content
        self.level = self._get_level(self.content)

    def _get_level(self, content) -> int:
        if content[:5] == "Error":
            return logging.ERROR
        else:
            return logging.WARNING


class SaxonLog:
    def __init__(self, log_output) -> None:
        self.saxon_output = log_output.decode()
        self.records = self._get_records()
        self.text = self._get_text()
        self.exit_code = self._create_exit_code(self.records)

    def _get_text(self) -> str:
        return "".join([record.content for record in self.records])

    def _get_records(self) -> List[SaxonRecord]:
        records = []
        for item in (e + "\n" for e in self.saxon_output.split("\n")):
            if item[:2] == "  ":
                records[-1].content += item
            else:
                record = SaxonRecord(item)
                records.append(record)
        return records

    def _create_exit_code(self, records) -> int:
        for record in records:
            if record.level == logging.ERROR:
                return 1
        return 0


class Tex:
    """Object handling the creation and processing of the TeX representation of the item."""

    def __init__(
        self,
        transcription: Union[LocalResource, RemoteResource, UrlResource],
        xslt_parameters: str = None,
        clean_whitespace: bool = True,
        enable_caching: bool = True,
        annotate_samewords: bool = True,
    ) -> None:
        self.id = transcription.id
        self.xml = transcription.file
        self.xslt = transcription.xslt
        self.digest = transcription.digest
        self.tmp_dir = transcription.tmp_dir
        self.cache = Cache(config.cache_dir) if enable_caching else None
        self.xslt_parameters = xslt_parameters
        self.clean_whitespace = clean_whitespace
        self.annotate_samewords = annotate_samewords

    def process(self, output_format):
        """Convert an XML file to TeX and compile it to PDF with XeLaTeX if required.

        Depending on the requested output format, this returns either a TeX file or a PDF file
        object.

        :return: File object.
        """
        output_file = self.clean(self.xml_to_tex())

        if output_format == "pdf":
            output_file = self.compile(output_file)

        return os.path.join(output_file)

    def xml_to_tex(self):
        """Convert the list of encoded files to tex, using the auxiliary XSLT script.

        The function creates a output dir in the current working dir and puts the tex file in that
        directory. The function requires saxon installed.

        Keyword Arguments:
        xml_buffer -- the content of the xml file under conversion
        xslt_script -- the content of the xslt script used for the conversion

        Return: File object.
        """

        if self.cache and self.cache.contains(basename=self.digest + ".tex"):
            logging.info(f"Using cached version of {self.id}.")
            return os.path.join(self.cache.dir, self.digest + ".tex")
        else:
            logging.info(f"Start conversion of {self.id}.")
            logging.debug(f"Using XSLT: {self.xslt}.")

            if self.xslt_parameters:
                process = subprocess.Popen(
                    [
                        "java",
                        "-jar",
                        os.path.join(config.module_dir, "vendor/saxon9he.jar"),
                        f"-s:{self.xml}",
                        f"-xsl:{self.xslt}",
                        self.xslt_parameters,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            else:
                process = subprocess.Popen(
                    [
                        "java",
                        "-jar",
                        os.path.join(config.module_dir, "vendor/saxon9he.jar"),
                        f"-s:{self.xml}",
                        f"-xsl:{self.xslt}",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            out, err = process.communicate()

            if err:
                logging.warning(
                    "The XSLT script reported the following warning(s):\n"
                    + err.decode("utf-8")
                )
            tex_buffer = out.decode("utf-8")
            logging.info("The XML was successfully converted to TeX.")

            tmp_filename = os.path.join(self.tmp_dir.name, self.digest + ".tex")
            with open(tmp_filename, mode="w+", encoding="utf-8") as fh:
                fh.write(tex_buffer)

            if self.cache:
                logging.debug("Storing file in cache.")
                filename = self.cache.store(fh.name, digest=self.digest, suffix=".tex")
            else:
                logging.debug("Storing file in current working directory.")
                filename = shutil.copyfile(
                    fh.name, os.path.join(os.path.curdir, self.digest + ".tex")
                )

            logging.debug("Cleaning up tmp dir.")
            self.tmp_dir.cleanup()

            return filename

    def whitespace_cleanup(self, tex_file: str) -> str:
        """Clean the content of the tex file for different whitespace problems.

        :return: File object of the tex file after cleanup.
        """

        logging.debug("Removing whitespace...")
        patterns = [
            # Remove redundant space around opening bracket.
            (r" ?{ ?", r"{"),
            # Remove redundant space before closing bracket.
            (r" }", r"}"),
            # Remove redundant space before punctuation.
            (r" ([.,?!:;]+)", r"\1"),
            # Remove space before empty lemma app notes.
            (r" (\\edtext{})", r"\1"),
            # Add missing space between adjacent app. notes.
            (r"}(\\edtext{[^}]+})", r"} \1"),
            # Remove excessive whitespace.
            (r" +", " "),
            # Remove redundant space between closing brackets. and punctuation.
            (r"} ([.,?!:;]+)", r"}\1"),
            # Remove leading space at beginning of line.
            (r"^ +", r""),
            # Remove trailing whitespace at paragraph end.
            (r" %$", "%"),
            # Remove trailing whitespace at opening parenthesis.
            (r"\( ", r"("),
            # Remove trailing whitespace at closing parenthesis.
            (r" \)", r")"),
            # Escape _ and ^ characters.
            (r"([_\^])", r"\\\1"),
            # Replace anything wrapped in quotes ("...") with \enquote{...}. This is a bit
            # dangerous as it assumes that the editor always balances his quotes,
            # and we cannot be sure of that. The proper way to do this would be with a stack
            # tracking opening and closing quotes and alerting user on unbalanced quotes.
            # That would of course require a separate function. Would it reduce performance
            # significantly?
            (r'"([^"]+?)"', r"\\enquote{\1}"),
        ]

        with open(tex_file) as f:
            buffer = f.read()

        for pattern, replacement in patterns:
            buffer = re.sub(pattern, replacement, buffer, flags=re.MULTILINE)

        with open(tex_file, "w") as f:
            f.write(buffer)

        logging.debug("Whitespace removed.")
        return tex_file

    def clean(self, tex_file):
        """Orchestrate cleanup of tex file.

        This is split into two subfunctions for maintainability.

        :return: File object of the text file after cleanup.
        """

        if self.clean_whitespace:
            tex_file = self.whitespace_cleanup(tex_file)

        if self.annotate_samewords:
            with open(tex_file) as f:
                buffer = f.read()

            buffer = samewords.core.process_string(buffer)

            with open(tex_file, "w") as f:
                f.write(buffer)

            logging.debug("Samewords added.")

        return tex_file

    def compile(self, input_file):
        """Convert a tex file to pdf with XeLaTeX.

        This requires `latexmk` and `xelatex`.

        :return: Pdf file object.
        """

        def read_output(pipe, func):
            for line in iter(pipe.readline, b""):
                func(line)
            pipe.close()

        def write_output(get):
            for line in iter(get, None):
                logging.info(line.decode("utf-8").replace("\n", ""))

        if self.cache.contains(self.digest + ".pdf"):
            logging.debug("Using cached pdf.")
            return os.path.join(self.cache.dir, self.digest + ".pdf")

        else:
            logging.info(f"Start compilation of {self.id}")
            process = subprocess.Popen(
                f"latexmk --xelatex --output-directory={self.tmp_dir.name} "
                f"--halt-on-error "
                f"{re.escape(input_file)}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                bufsize=1,
            )
            q = queue.Queue()
            out_thread = threading.Thread(
                target=read_output, args=(process.stdout, q.put)
            )
            err_thread = threading.Thread(
                target=read_output, args=(process.stderr, q.put)
            )
            write_thread = threading.Thread(target=write_output, args=(q.get,))

            for t in (out_thread, err_thread, write_thread):
                t.start()

            process.wait()
            q.put(None)

            if process.returncode == 0:
                # Process finished. We clean the tex dir and return the filename.
                output_file = os.path.join(
                    self.tmp_dir.name,
                    os.path.splitext(os.path.basename(input_file))[0] + ".pdf",
                )
                cache_name = self.cache.store(
                    output_file, digest=self.digest, resource_id=self.id, suffix=".pdf"
                )
                return cache_name
            else:
                logging.error(
                    "The compilation failed. See tex output above for more info."
                )
                raise Exception("Latex compilation failed.")
