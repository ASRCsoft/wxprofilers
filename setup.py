from __future__ import absolute_import
from Cython.Build import cythonize
from numpy.distutils.misc_util import Configuration
from numpy.distutils.core import setup


import os
if os.environ.get('READTHEDOCS') == 'True':
    # link to the conda fortran compiler for readthedocs
    file_path = os.path.realpath(__file__)
    checkout_name = os.path.basename(os.path.dirname(file_path))
    gfortran_rel_path = '../../conda/' + checkout_name + '/bin/x86_64-conda_cos6-linux-gnu-gfortran'
    gfortran_path = os.path.realpath(gfortran_rel_path)
    os.environ['F77'] = gfortran_path
    os.environ['F90'] = gfortran_path
    

def configuration(parent_package='', top_path=None):
    config = Configuration(package_name='wxprofilers', package_path='wxprofilers')
    config.add_extension('_cape', sources=['src/getcape.f90'])
    config.add_extension('_median', sources=['src/filter.cc'], language='C++')
    config.add_subpackage('_segmentation', subpackage_path='wxprofilers/_segmentation')
    config.add_subpackage('sonde', subpackage_path='wxprofilers/sonde')
    config.add_subpackage('sonde/_sondepbl', subpackage_path='wxprofilers/sonde/_sondepbl')
    config.add_library('BUFR_1_07_1', sources=['src/BUFR_1_07_1.f'])
    config.add_extension('_rrs_decoder', sources=['src/RRS_Decoder_1_04.f'],
                         libraries=['BUFR_1_07_1'])
    config.ext_modules += cythonize("wxprofilers/_uniform.pyx")
    return config


setup(version='0.1dev',
      description='Utilities for working with weather profiler instruments',
      url='https://github.com/ASRCsoft/wxprofilers',
      author='William May',
      author_email='wcmay@albany.edu',
      test_suite='nose.collector',
      tests_require=['nose'],
      install_requires=[
          'cython',
          'matplotlib',
          'metpy',
          'nipy',
          'numpy',
          'pandas',
          'scipy',
          'statsmodels',
          'xarray'
      ],
      **configuration(top_path='').todict()
)
