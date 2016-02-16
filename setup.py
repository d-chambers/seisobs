# -*- coding: utf-8 -*-
"""
@author: Derrick
"""

from setuptools import setup, find_packages


setup(
    name='seisobs',

    version = '0.0.2',

    description = 'A package for converting s-files to obspy catalog objects',
    
    # The project's main homepage.
    url = 'https://github.com/d-chambers/seisobs',

    # Author details
    author = 'Derrick Chambers',
    author_email = 'djachambeador@gmail.com',

    # Liscense
    license = 'MIT',

    classifiers = [

        'Development Status :: 3 - Alpha',
        'Intended Audience :: Geo-scientists',
        'Topic :: Earthquake metadata conversion',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords = 'seismology',
    packages = find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires = ['pytest', 'obspy', 'pandas >= 0.17.0', 'ipdb']
)
