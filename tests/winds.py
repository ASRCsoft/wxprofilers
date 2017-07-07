import unittest
from unittest import TestCase

import numpy as np
import xarray as xr
import rasppy

# prepare the test data
lidar = xr.open_dataset('test_data.nc')
# get rid of silly byte strings that xarray created
lidar.coords['Component'].values = list(map(lambda x: x.decode(), lidar.coords['Component'].values))
lidar['wspeed2'] = lidar.rasp.estimate_wind()

class TestWinds(TestCase):    
    def test_wind_estimate_is_close(self):
        self.assertTrue((lidar['Windspeed'] - lidar['wspeed2']).max().values < .002)
        
    def test_same_nans(self):
        wspeed1 = lidar['Windspeed'].isel(Time=range(4, lidar.dims['Time']))
        wspeed2 = lidar['wspeed2'].isel(Time=range(4, lidar.dims['Time']))
        self.assertTrue(np.all(np.equal(np.isnan(wspeed1), np.isnan(wspeed1))))

if __name__ == '__main__':
    unittest.main()
