Radiosondes
===========

Functions for converting radiosonde files to ``xarray`` datasets are
in the ``wxprofilers.sonde`` module.

.. code-block:: python

   import wxprofilers.sonde as sonde

NWS BUFR files
--------------

``wxprofilers`` includes the National Climatic Data Center (NCDC)'s
`RRS Decoder
<ftp://ftp.ncdc.noaa.gov/pub/data/ua/rrs-data/readme.txt>`_ to extract
text files from binary radiosonde BUFR files.

.. code-block:: python
	     
   sonde.decode_rrs('94983_2005102412', '56')
