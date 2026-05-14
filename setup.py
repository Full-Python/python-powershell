#!python
"""A setuptools based setup module.

ToDo:
- Everything
"""

from setuptools import setup

from simplifiedapp import object_metadata

import powershell

setup(**object_metadata(powershell))