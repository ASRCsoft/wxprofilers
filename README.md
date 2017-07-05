# raspPy
Python package with utilities for Lidar and other weather profile instruments

## Documentation
[rasppy.readthedocs.io/en/latest/](http://rasppy.readthedocs.io/en/latest/)

## Installation
raspPy can be installed with pip:

```bash
pip install git+https://github.com/ASRCsoft/raspPy.git
```

## Usage
Generate xarray/raspPy objects from lidar text files:

```python
import rasppy.convert as rasp
lidar = rasp.lidar_from_csv('radial_wind_data.csv', scan='scan.xml', wind='reconstruction_wind_data.csv')
```
