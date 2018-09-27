#!/usr/bin/env python

from __future__ import absolute_import
from distutils.core import setup


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
          'cython',
          'matplotlib',
          'xarray',
          'metpy',
          'statsmodels',
          'nipy'
      ]
)


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('rasppy', parent_package, top_path)
    config.add_extension('cape', sources=['src/cape.pyf', 'src/cape.f90'])
    config.add_extension('median', sources=['src/filter.cc'])
    config.add_subpackage('segmentation', subpackage_path='rasppy/segmentation')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
