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

      description='Script for compiling LombardPress encoded XML documents to TeX and PDF.',
      url='https://github.com/stenskjaer/lbp_print',
      author='Michael Stenskjær Christensen',
      author_email='michael.stenskjaer@gmail.com',
      license='MIT',
)
