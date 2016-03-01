# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 14:07:03 2016

@author: derrick
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import seisobs.core
import seisobs.specs
import seisobs

import os
# get version
pkg_dir = os.path.dirname(seisobs.__file__)
version_fil = os.path.join(pkg_dir, 'version.py')
with open(version_fil) as verfi:
    __version__ = verfi.read().strip()

# bring a few key objects to front
Seisob = seisobs.core.Seisob
seis2cat = seisobs.core.seis2cat
seis2disk = seisobs.core.seis2disk
