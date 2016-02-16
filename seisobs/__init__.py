# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 14:07:03 2016

@author: derrick
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import seisobs.core
import seisobs.specs

# bring a few key objects to front
Seisob = seisobs.core.Seisob
seis2cat = seisobs.core.seis2cat
seis2dist = seisobs.core.seis2disk