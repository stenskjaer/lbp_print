`lbp_print` is a small utility for processing a LombardPress valid XML text with
a relevant XSLT script and compile to PDF with XeLaTeX.

# Requirements

The script makes use of *XeLaTeX* and *SaxonHE*. Currently, *Saxon* is included
in the vendor directory, but Java Runtime Environment must be installed to run
it. One might consider going over to
the [pysaxon module](https://github.com/ajelenak/pysaxon).

Aside from that, there are also some internal dependencies, specified in the
`requirements.txt` file.
