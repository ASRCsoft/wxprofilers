import numpy as np
import pandas as pd
import xarray as xr

class ProfileInstrument(object):
    def __init__(self, tsdict, profiles=None, latitude=None, longitude=None, elevation=None, xarray=None):
        self.data = tsdict
        self.profiles=profiles
        self.latitude=latitude
        self.longitude=longitude
        self.elevation=elevation
        self.wind=None
        self.xarray = xarray
        # new!
        # h1 = {}
        # print(self.data.columns.levels[0])
        # for level in self.data.columns.levels[0]:
        #     h1[level] = pd.DataFrame(self.data[level])
        # self.xarray = xr.Dataset(h1)
        #self.xarray = xr.Dataset.from_dataframe(tsdict)

    def export(self):
        # write a CF-compliant netCDF file containing the profileInstrument data
        pass

    def writeRAOB(self, time, filename, temp='Temperature (K)', rh='Relative Humidity (%)',
                  vap_den=None, liq_wat=None, wind=True, wspeed=True):
        # set up the header information
        header_lines = []
        header_lines.append('RAOB/CSV, ' + 'Example Data from microwave radiometer and lidar')
        # header_lines.append('INFO:1, ' + 'First line of freeform text')
        # header_lines.append('INFO:2, ' + 'Another freeform text line')
        header_lines.append('DTG, ' + str(time))
        if self.latitude is not None: header_lines.append('LAT, ' + str(self.latitude) + ', N')
        if self.longitude is not None: header_lines.append('LON, ' + str(self.longitude) + ', W')
        if self.elevation is not None: header_lines.append('ELEV, ' + str(self.elevation) + ', M')
        # skip for now
        # header_lines.append('WMO, 12345')
        header_lines.append('TEMPERATURE, K')
        header_lines.append('MOISTURE, RH')
        # skip for now
        if wind: header_lines.append('WIND, m/s U/V')
        # wind height type is 'Above Ground Level' for now
        header_lines.append('GPM, AGL')
        header_lines.append('MISSING, -999')
        # what?
        # header_lines.append('SORT, YES')
        # in case of ozone:
        # header_lines.append('OZONE, mPa')
        # not now:
        # header_lines.append('EXTRA#1, Extra#1Name, Extra#1Units')
        # header_lines.append('EXTRA#2, Extra#2Name, Extra#2Units')
        # header_lines.append('SCALAR#1, Scalar#1Name, Scalar#1Value, Scalar#1Units')
        # header_lines.append('SCALAR#2, Scalar#2Name, Scalar#2Value, Scalar#2Units')
        header_lines.append('RAOB/DATA\n')
        header = '\n'.join(header_lines)

        # set up the data (making sure to round as required)
        levels = self.data[temp].columns
        if len(levels) < 2:
            print('Must have at least 2 levels of data')
            exit()
        if wind:
            columns = ['PRES', 'TEMP', 'RH', 'UU', 'VV', 'GPM']
        else:
            columns = ['PRES', 'TEMP', 'RH', 'WIND', 'SPEED', 'GPM']
        df = pd.DataFrame(index = levels, columns = columns)
        df['TEMP'] = self.data[temp].loc[time].map(lambda x: round(x, 1))
        df['RH'] = self.data[rh].loc[time].map(lambda x: round(x, 1))
        # df['WIND'] = np.nan
        # df['SPEED'] = np.nan
        df['GPM'] = map(int, map(lambda x: round(x), 1000 * self.data[temp].columns.map(float)))
        df['PRES'] = (1013.25 * np.exp(-df['GPM'] / 7000)).map(lambda x: round(x, 1))
        if vap_den is not None: df['VapDen'] = self.data[vap_den].loc[time].map(lambda x: round(x, 3))
        if liq_wat is not None: df['LiqWat'] = self.data[liq_wat].loc[time].map(lambda x: round(x, 3))
        if self.wind is not None:
            if wind:
                df['UU'] = (-self.wind.speed.loc[time, 'y']).map(lambda x: round(x, 1))
                df['VV'] = (-self.wind.speed.loc[time, 'z']).map(lambda x: round(x, 1))
            if wspeed:
                df['WSPEED'] = (-self.wind.speed.loc[time, 'z']).map(lambda x: round(x, 1))


        #print(df)

        roab_file = open(filename, "w")
        roab_file.writelines(header)
        roab_file.close()
        # print(df.head())
        # exit()
        df.to_csv(filename, na_rep=-999, index=False, mode='a')

    # def __getattr__(self, item):
    #     print(item)
    #     print(self.data.values[0].__getattr__(item))
    #     # run the given function on each ProfileTimeSeries in self.data
    #     for key in self.data.keys():
    #         code = 'self.data["' + key + '"] = self.data["' + key + '"].' + item
    #         print(code)
    #         exec(code)