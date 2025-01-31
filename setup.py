#!/usr/bin/env python
from __future__ import absolute_import
from distutils.core import setup,Extension
import sys

setup(
  name='FitAllB',
  version='1.1.0',
  description='Fitting routines for global parameters (fitgloball), global parameters for each grain (fitglobalgrain) and grain cms, orientations and strain (fitallb)',
  license='GPL', maintainer='Jette Oddershede',
  maintainer_email='jeto@fysik.dtu.dk',
  url='http://fable.wiki.sourceforge.net',
  packages=["FitAllB"],
  package_dir={"FitAllB":"FitAllB"},
  scripts=["scripts/fitallb.py","scripts/fitgloball.py","scripts/fitglobalgrain.py","scripts/fitgloball_multidet.py"]
)
