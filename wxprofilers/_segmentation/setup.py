from __future__ import absolute_import
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
from Cython.Build import cythonize
from numpy.distutils.misc_util import Configuration
from numpy.distutils.core import setup, Extension

sourcefiles = ['wxprofilers/_segmentation/_segmentation.pyx',
               'wxprofilers/_segmentation/mrf.c']

extensions = [Extension("wxprofilers._segmentation._segmentation",
                        sourcefiles)]

setup(
    packages=['wxprofilers._segmentation'],
    ext_modules = cythonize(extensions),
    include_dirs=[np.get_include()]
)
