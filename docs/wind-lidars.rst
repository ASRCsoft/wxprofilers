Wind Lidars
===========

Functions for converting wind lidar files to ``xarray`` datasets are
in the ``wxprofilers.convert`` module.

.. code-block:: python

   import wxprofilers.convert as wxp

NYS Mesonet csv files
---------------------

.. code-block:: python
	     
   lidar = wxp.lidar_from_csv(rws='20170225_whole_radial_wind_data.csv',
	                      scans='20170225_scan.xml',
                              wind='20170225_reconstruction_wind_data.csv')
