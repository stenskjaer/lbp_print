`lbp_print` is a small utility for processing a LombardPress valid XML text with
a relevant XSLT script and compile to PDF with XeLaTeX.


# Installation

Download the repo. Notice that the xslt is included as submodule
of [lbp-print-xslt](https://github.com/lombardpress/lbp-print-xslt), so include
it in cloning by using `--recursive`.
```
git clone --recursive https://github.com/stenskjaer/lbp_print.git
```

The script requires Python 3.6 installed in your system. If you are on a Mac OSX
machine, and you use [Homebrew](https://brew.sh/), you can run `brew install
python3`. If you do not use Homebrew, download the (latest official python
distribution)[https://www.python.org/downloads/] and follow the instructions.

## Temporary testing

This solution is good for testing, development and if you would like to try out
the script without installing anything permanently on your system,
a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
setup is the best solution. All the help you need should be in the linked guide.

To create a virtual environment for the project, run:
```bash
$ mkvirtualenv -p python3 <name>
```

Where `<name>` is the name you want to give the venv.

After activating the virtual environment (`workon` or `source`), install dependencies:
```bash
$ pip3 install -r requirements.txt
```

Now you should be able to run the script (while the virtual environment is
activated) by pointing to its location. If you are in the project directory,
just try running:
```bash
$ ./lbp_print.py pdf --scta http://scta.info/resource/lectio1
```
You should now be able to find the result in the directory *output*.


## System install

If you would like to install the script for general usage on you system, you
should run the command 
```bash
python3 setup.py install
```

Now try:
```bash
$ lbp_print.py pdf --scta http://scta.info/resource/lectio1
```
This will, as default, put the results in a directory called `output` in the
directory where you call the command.

## Requirements

Aside from Python3.6 (and other packaged dependencies), the script makes use of
*XeLaTeX* and *SaxonHE*. *Saxon* is included in the vendor directory,
but Java Runtime Environment on the system to run it. One might consider
going over to the [pysaxon module](https://github.com/ajelenak/pysaxon). You
also need to have a installation of *XeLaTeX*.

