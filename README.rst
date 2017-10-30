``lbp_print`` is a small utility for processing a LombardPress valid XML
text with a relevant XSLT script and compile to PDF with XeLaTeX.

Installation
============

The script requires Python 3.6 installed in your system. If you are on a
Mac OSX machine, and you use `Homebrew <https://brew.sh/>`__, you can
run ``brew install python3``. If you do not use Homebrew, download the
`latest official python
distribution <https://www.python.org/downloads/>`__ and follow the
instructions.

The simplest way to install it is via pypi:

.. code:: bash

    pip3 install lbp_print

It will most likely throw an error that it cannot find a version
satisfying ``lbppy>=0.0.0 (from lbp_print)``. You solve that by first
installing ``lbbpy`` from the Github repository:

.. code:: bash

    pip3 install git+https://github.com/lombardpress/lbppy.git@master#egg=lbppy

If you want to clone the repository, notice that the xslt is included as
submodule of
`lbp-print-xslt <https://github.com/lombardpress/lbp-print-xslt>`__, so
you need to clone with the ``--recursive`` flag.

.. code:: bash

    git clone --recursive https://github.com/stenskjaer/lbp_print.git

Temporary testing
-----------------

If you want to test or hack on the package, or if you would like to try
out the script without installing anything permanently on your system, a
`virtual
environment <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`__
setup is the best solution.

To create a virtual environment for the project, run:

.. code:: bash

    $ python3 -m venv <name>

Where ``<name>`` is the name you want to give the venv. A typical
practice is to name it ``.env`` or something like that. It will create a
directory in the root of the project directory called ``.env`` which
contains the environment.

Now activate the environment:

.. code:: bash

    $ source .env/bin/activate

And install dependencies the dependencies of the script:

.. code:: bash

    $ pip3 install -r requirements.txt

Now you can make the package globally available (in the virtual
environment, if you want), but use the ``-e`` flag during installation
to symlink the source files and the global CLI. Then if you make any
changes in the script, it is available in the global CLI. Try it with
(from the base dir of the package):

.. code:: bash

    pip install -e .

Now you should be able to run the script (while the virtual environment
is activated) with the following command:

.. code:: bash

    $ lbp_print pdf --scta http://scta.info/resource/lectio1

You should now be able to find the result in the directory *output* in
the current working dir.

When you are done, you can reset your system to the state before
testing, deactivate the virtual environment. If you never want to use
the script again, remove the directory of the environment (possibly with
``rmvirtualenv`` if you have installed ``virtualenvwrapper``) and remove
the directory created by the ``git clone`` command.

System install
--------------

If you would like to install the script for general usage on you system,
you should run the command

.. code:: bash

    python3 setup.py install

Now try:

.. code:: bash

    $ lbp_print.py pdf --scta http://scta.info/resource/lectio1

This will, as default, put the results in a directory called ``output``
in the directory where you call the command.

Requirements
------------

Aside from Python3.6 (and other packaged dependencies), the script makes
use of *XeLaTeX* and *SaxonHE*. *Saxon* is included in the vendor
directory, but Java Runtime Environment on the system to run it. One
might consider going over to the `pysaxon
module <https://github.com/ajelenak/pysaxon>`__. You also need to have a
installation of *XeLaTeX*.

Usage
=====

The script has two main command ``tex`` and ``pdf``, determining which
type of output you want. If you want to use a local file, you should use
the ``--local`` flag and let the ``<file>`` be the location of a
local file, otherwise you can enable the ``--scta`` flag and let the
identifier be an id in the SCTA database.

To get a full overview of the options and possible commands, run
``lbp_print --help``. This will produce this usage guide:

::

    Usage:
      lbp_print (tex|pdf) [options] --local <file>...
      lbp_print (tex|pdf) [options] --scta <id>...
      lbp_print recipe <recipe> [options]

    Pull LBP-compliant files from SCTA repositories or use local, convert them into
    tex or pdf.

    Arguments:
      <file>                   File location of one or more objects to be processed.
      <id>                     SCTA id of one or more objects to be processed.

    Multiple arguments are separated with whitespace.

    Commands:
      tex                      Convert the xml to a tex-file.
      pdf                      Convert the xml to a tex-file and compile it into a
                               pdf.
      recipe <recipe>          Follow recipe in config file in <recipe>.

    Options:
      --scta                   Flag. When present, the <id> should be an
                               expression id of the SCTA database.
      --local                  Flag. When present, process local file indicated
                               by <file> argument.
      --xslt <file>            Use a custom xslt file in place of the default
                               supplied templates.
      --output, -o <dir>       Put results in the specified directory.
                               [default: .]
      --cache-dir <dir>        The directory where cached files should be stored.
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

Unless you specify an output directory with ``--output``, the script
will put the resulting file in the current working directory. This means
that if you are on the Desktop when calling the script from the command
line, that is where the file will land after processing.

Config files
------------

If you keep passing the same arguments to the script, for instance to
your own custom xslt script, you might want to use a config file.

The config file is written in JSON format.

By default the script looks for at configuration file with the name
``~/.lbp_print.json``, but if you pass another file path in the
``--config-file`` argument, it will look in that location.

The default configuration file of the standard options looks like this:

.. code:: json

    {
        "--output": ".",
        "--config-file": "~/.lbp_print.json",
        "--verbosity": "info"
    }

The arguments must be the long form identical to the specification in
the ``lbp_print --help`` description. This means that options must have
prepended ``--``, arguments wrapped in ``<>`` and commands without any
wrapping.

Recipes
-------

You can create full configuration files describing all relevant command
line arguments for creating a specific result and pass that file along
with the ``recipe`` command.

For example, running this command:

.. code:: bash

    lbp_print recipe ~/Desktop/lbp.json

Where the content of ``~/Desktop/lbp.json`` is

.. code:: json

    {
        "--local": true,
        "<file>": [
            "~/Transcriptions/49-prooemium/da-49-prooemium.xml",
            "~/Transcriptions/49-l1q1/da-49-l1q1.xml",
            "~/Transcriptions/49-l3q15/da-49-l3q15.xml"
        ],
        "--output": "~/Desktop/testing",
        "--verbosity": "debug"
    }

Is equivalent to running

.. code:: bash

    lbp_print pdf --output ~/Desktop/testing --verbosity debug \
        --local ~/Transcriptions/49-prooemium/da-49-prooemium.xml \
        ~/Transcriptions/49-l1q1/da-49-l1q1.xml \
        ~/Transcriptions/49-l3q15/da-49-l3q15.xml

Such recipes can be very useful when creating the same group of items
with a specific configuration multiple times with good confidence that
the configuration is stable.

Caching
-------

The module includes a caching feature. It is disabled by default, but if
you regularly process the same files (either from remote or local
sources), this can save you a lot of waiting time.

When you configure a cache directory with the option ``--cache-dir``,
all completed files will be stored there and reused whenever the you
input an exactly identical file to be compiled with exactly the same
xslt script.

It works as follows. Whenever an XML file is received, and the proper
XSLT conversion script is identified, a unique hash value is computed
based on the content of those two files. This means that as soon as one
of those two files changes a completely new hash value is produced.
Completed ``tex`` and ``pdf`` files are stored in the ``--cache-dir``
(using the hash value and file extension as basename). Before any
processing the script checks whether a file with the current hash value
is present in the cache. If it finds something, it returns that to you
and saves you the waiting time of compilation (especially ``tex``
compilations can take annoyingly long time).

The caching system makes sure that only the most recent version of every
file (based on resource id or file name) is stored to make sure it does
not swell completely out of proportion. But this also means that the
system will identify two files with the same filename (not full path,
only the name of the file, such as ``Jandun, question 2.24.xml``) as the
same and remove the previous of the two from the cache. This will
therefore lead to redundant rebuilding and caching when you compile
different files with the same basename.
