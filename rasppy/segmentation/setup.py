from __future__ import absolute_import
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
from distutils.core import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

sourcefiles = ['rasppy/segmentation/_segmentation.pyx',
               'rasppy/segmentation/mrf.c']

extensions = [Extension("rasppy.segmentation._segmentation",
                        sourcefiles)]

setup(
    packages=['rasppy.segmentation'],
    ext_modules = cythonize(extensions),
    include_dirs=[np.get_include()]
)
