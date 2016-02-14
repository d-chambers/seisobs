# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 14:07:03 2016

@author: derrick
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import seisobs.core
import seisobs.specs
import sys


def deb(*args):
    global de
    de = args
    sys.exit(1)
    
Seisob = seisobs.core.Seisob