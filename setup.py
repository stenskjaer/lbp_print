# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

from lbp_print import __version__

setup(name='lbp_print',
      version=__version__,
      packages=find_packages(),
      scripts=['lbp_print.py'],
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
      ],

      description='Collection of utility scripts for handling LombardPress material.',
      url='https://github.com/stenskjaer/lbp_print',
      author='Michael Stenskjær Christensen',
      author_email='michael.stenskjaer@gmail.com',
      license='MIT',
)