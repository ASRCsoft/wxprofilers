from __future__ import absolute_import
from Cython.Build import cythonize


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('wxprofilers', parent_package, top_path)
    config.add_extension('cape', sources=['src/cape.pyf', 'src/cape.f90'])
    config.add_extension('median', sources=['src/filter.cc'], language='C++')
    config.add_subpackage('segmentation', subpackage_path='wxprofilers/segmentation')
    config.add_library('BUFR_1_07_1', sources=['src/BUFR_1_07_1.f'])
    config.add_extension('rrs_', sources=['src/RRS_Decoder_1_04.f'],
                         libraries=['BUFR_1_07_1'])
    config.ext_modules += cythonize("wxprofilers/uniform.pyx")
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(version='0.1dev',
          description='Utilities for working with weather profile data with xarray',
          url='https://github.com/ASRCsoft/ipas_python',
          author='William May',
          author_email='williamcmay@live.com',
          test_suite='nose.collector',
          tests_require=['nose'],
          install_requires=[
              'cython',
              'matplotlib',
              'xarray',
              'metpy',
              'statsmodels',
              'nipy'
          ],
          **configuration(top_path='').todict()
    )
