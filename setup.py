#!/usr/bin/env python

from distutils.core import setup
from distutils.core import Extension

setup(name='raspPy',
      version='0.1dev',
      description='Utilities for working with weather profile data with xarray',
      url='https://github.com/ASRCsoft/ipas_python',
      author='William May',
      author_email='williamcmay@live.com',
      packages=['rasppy'],
      test_suite='nose.collector',
      tests_require=['nose'],
      install_requires=[
          'xarray',
          'metpy',
          'statsmodels'
      ]
)


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('rasppy', parent_package, top_path)
    config.add_extension('cape', sources=['src/cape.pyf','src/cape.f90'])
    config.add_extension('rrs', sources=['src/rrs.pyf','src/BUFR_1_07_1.f', 'src/RRS_Decoder_1_04.f', 'src/unixbufr.f'])
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
