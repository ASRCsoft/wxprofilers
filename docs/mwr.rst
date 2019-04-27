Microwave Radiometers
=====================

Functions for converting microwave radiometer files to ``xarray``
datasets are in the ``wxprofilers.convert`` module.

.. code-block:: python

   import wxprofilers.convert as wxp

NYS Mesonet Microwave Radiometer csv Files
------------------------------------------

.. code-block:: python
	     
   mwr = wxp.mwr_from_csv('2017-02-25_00-04-11_lv2.csv', resample='5T')
