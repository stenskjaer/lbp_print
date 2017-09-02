# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


about = {}
with open(os.path.join('lbp_print', '__about__.py')) as fp:
    exec(fp.read(), about)

setup(name='lbp_print',
      version=about['__version__'],
      packages=find_packages(),
      dependency_links=[
          "git+https://github.com/lombardpress/lbppy.git@f272e44429fcbd3f19384471c9cfb3903100fb30#egg=lbppy",
      ],
      tests_require=[
          'pytest==3.1.3',
      ],
      install_requires=[
          'docopt==0.6.2',
          'isodate==0.5.4',
          'lbppy>=0.0.0',
          'lxml==3.7.3',
          'pyparsing==2.2.0',
          'rdflib==4.2.2',
          'SPARQLWrapper==1.8.0',
          'untangle==1.1.0',
      ],
      classifiers=[
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Topic :: Text Processing :: Markup :: XML',
          'Topic :: Text Processing :: Markup :: LaTeX',
      ],
      entry_points={
          'console_scripts': ['lbp_print=lbp_print.cli:main']
      },
      include_package_data=True,

      description='Script for compiling LombardPress encoded XML documents to '
                  'TeX and PDF.',
      long_description='``lbp_print`` is a small utility for processing a '
                       'LombardPress valid XML text with a relevant XSLT '
                       'script and compile to PDF with XeLaTeX. For more '
                       'info, see `the Github page '
                       '<https://github.com/stenskjaer/lbp_print>`__',
      url='https://github.com/stenskjaer/lbp_print',
      author='Michael Stenskjær Christensen',
      author_email='michael.stenskjaer@gmail.com',
      license='MIT',
)
