# wxprofilers
Python package with utilities for weather profiler instruments

## Documentation
[wxprofilers.readthedocs.io/en/latest/](http://wxprofilers.readthedocs.io/en/latest/)

(It's a work in progress.)

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
