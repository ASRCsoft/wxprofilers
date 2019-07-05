# wxprofilers

[![Documentation Status](https://readthedocs.org/projects/wxprofilers/badge/?version=latest)](https://wxprofilers.readthedocs.io/en/latest/?badge=latest)

Python package with utilities for weather profiler instruments

## Documentation
[wxprofilers.readthedocs.io/en/latest/](http://wxprofilers.readthedocs.io/en/latest/)

## Installation
wxprofilers can be installed with pip:

```bash
pip install git+https://github.com/ASRCsoft/wxprofilers.git
```

## Usage
Generate xarray objects from lidar text files:

```python
import wxprofilers.convert as wxp
lidar = wxp.lidar_from_csv('radial_wind_data.csv', scan='scan.xml', wind='reconstruction_wind_data.csv')
```
