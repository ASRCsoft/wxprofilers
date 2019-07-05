from __future__ import absolute_import
import os
from setuptools import find_packages
from Cython.Build import cythonize
from numpy.distutils.core import setup, Extension


if os.environ.get('READTHEDOCS') == 'True':
    # print some helpful readthedocs debugging info:
    print('------ setup.py for readthedocs ------')
    import sys
    print('python: ' + sys.version)
    import numpy as np
    print('numpy: ' + np.__version__)
    import cython
    print('cython: ' + cython.__version__)
    print('--------------------------------------')
    # link to the conda fortran compiler for readthedocs
    file_path = os.path.realpath(__file__)
    checkout_name = os.path.basename(os.path.dirname(file_path))
    gfortran_rel_path = '../../conda/' + checkout_name + '/bin/x86_64-conda_cos6-linux-gnu-gfortran'
    gfortran_path = os.path.realpath(gfortran_rel_path)
    os.environ['F77'] = gfortran_path
    os.environ['F90'] = gfortran_path
    # remove some package dependencies
    install_requires=[
        'cython',
        'numpy'
    ]
else:
    install_requires=[
        'cython',
        'matplotlib',
        'metpy',
        'numpy',
        'pandas',
        'scipy',
        'statsmodels',
        'xarray'
    ]

# organize libraries and extensions
bufr_lib = ('BUFR_1_07_1',
            {'depends': [], 'sources': ['src/BUFR_1_07_1.f']})
exts = [
    Extension('_cape', ['src/getcape.f90']),
    Extension('_median', ['src/filter.cc'], language='c++'),
    Extension('_rrs_decoder', ['src/RRS_Decoder_1_04.f'],
              libraries=['BUFR_1_07_1'])
]
seg_ext = Extension('_segmentation._segmentation',
                    ['wxprofilers/_segmentation/_segmentation.pyx',
                     'wxprofilers/_segmentation/mrf.c'])
exts += cythonize([seg_ext, 'wxprofilers/_uniform.pyx'])

setup(name='wxprofilers',
      version='0.1dev',
      description='Utilities for working with weather profiler instruments',
      url='https://github.com/ASRCsoft/wxprofilers',
      author='William May',
      author_email='wcmay@albany.edu',
      packages=find_packages(),
      libraries=[bufr_lib],
      ext_modules=exts,
      install_requires=install_requires,
      test_suite='nose.collector',
      tests_require=['nose']
)
