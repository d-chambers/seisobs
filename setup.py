# -*- coding: utf-8 -*-
"""
@author: Derrick
"""

from setuptools import setup, find_packages
import os

version_file = os.path.join('nispy', 'version.txt')
with open(version_file) as vf:
    __version__ = vf.read().strip()

setup(
    name='seisobs',
    version = __version__,
    description = 'A package for converting s-files to obspy catalog objects',
    url = 'https://github.com/d-chambers/seisobs',
    author = 'Derrick Chambers',
    author_email = 'djachambeador@gmail.com',
    license = 'MIT',
    classifiers = [

        'Development Status :: 3 - Alpha',
        'Intended Audience :: Geo-scientists',
        'Topic :: Earthquake metadata conversion',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords = 'seismology',
    packages = find_packages(exclude=['contrib', 'docs', 'Tests*']),
    install_requires = ['pytest', 'obspy >= 1.0.0', 'pandas >= 0.17.0']
)
