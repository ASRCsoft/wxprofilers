Converting data
===============

In order to use the raspPy and xarray tools, data must be stored as
xarray objects. Functions for converting data to xarray format are in
the ``rasppy.convert`` module.

.. ipython:: python

   import rasppy.convert as rasp

Lidar csv files
---------------

.. ipython:: python
	     
   lidar = rasp.lidar_from_csv(rws='20170225_whole_radial_wind_data.csv',
	                       scans='20170225_scan.xml',
                               wind='20170225_reconstruction_wind_data.csv')
   lidar


Microwave radiometer csv files
------------------------------

.. ipython:: python
	     
   mwr = rasp.mwr_from_csv('2017-02-25_00-04-11_lv2.csv', resample='5T')
   mwr
