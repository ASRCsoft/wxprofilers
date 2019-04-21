# wxprofilers
Python package with utilities for weather profiler instruments

## Documentation
[rasppy.readthedocs.io/en/latest/](http://rasppy.readthedocs.io/en/latest/)

## Installation
wxprofilers can be installed with pip:

```bash
pip install git+https://github.com/ASRCsoft/wxprofilers.git
```

## Usage
Generate xarray objects from lidar text files:

```python
import wxprofilers.convert as rasp
lidar = rasp.lidar_from_csv('radial_wind_data.csv', scan='scan.xml', wind='reconstruction_wind_data.csv')
```
