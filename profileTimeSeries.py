'''
This file uses the dataframe with time index
Main use is for plotting heatmaps using matplotlib
Includes the core functions handling the data
for plotting and aggregating by time
'''
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#import matplotlib.image as mpimg
import matplotlib.dates as mdates
#import copy
import misc as rasp

# rewriting as an xarray module, following the guidelines here:
# http://xarray.pydata.org/en/stable/internals.html#extending-xarray
import xarray as xr

@xr.register_dataset_accessor('rasp')
class ProfileDataset(object):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def estimate_wind_leosphere(self, rws='RWS', status='Status'):
        if (self._obj[status] is None or self._obj[rws] is None or 'LOS ID' not in self._obj.coords.keys()):
            # raise an error
            pass

        el = float(self._obj.attrs['scan']['elevation_angle_deg']) * math.pi / 180

        # create the multiIndex ProfileTimeSeries
        #rws_cols = self.data[rws].columns
        rws_cols = self._obj.coords['Range'].values
        iterables = [['x', 'y', 'z'], rws_cols]
        mult_index = pd.MultiIndex.from_product(iterables, names=['Component', 'Range'])
        winds = pd.DataFrame(index=self._obj.coords['Timestamp'].to_index(), columns=mult_index, dtype='float')

        #status_mat = self.data[status].as_matrix()
        status_mat = self._obj[status].values
        is_good = (status_mat[0:-4,:] + status_mat[1:-3,:] + status_mat[2:-2,:] +
                   status_mat[3:-1,:] + status_mat[4:,:]) > 4.9

        good_indices = np.where(is_good)
        # add 4 columns for the 4 removed earlier
        good_indices = (good_indices[0] + 4, good_indices[1])
        row_los = self._obj.coords['LOS ID'][good_indices[0]].astype(int).values

        rws_mat = pd.DataFrame(self._obj[rws].values, index=self._obj.coords['Timestamp'].values, columns=rws_cols)
        good_cols = rws_cols[good_indices[1]]
        los0 = rws_mat.lookup(rws_mat.index[good_indices[0] - row_los], good_cols)
        los1 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 4) % 5)], good_cols)
        los2 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 3) % 5)], good_cols)
        los3 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 2) % 5)], good_cols)
        los4 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 1) % 5)], good_cols)

        xs = (los2 - los0) / (2 * math.cos(el))
        ys = (los3 - los1) / (2 * math.cos(el))
        zs = (los0 + los1 + los2 + los3) * .789 / (4 * math.sin(el)) + los4 * .211

        # YAAAAAAAAAAAAAAAAAAAAAAAYYYYYYYYYYYYYYYY it works!!!!!!!!!!
        for col in range(self._obj[rws].shape[1]):
            col_indices = np.where(good_indices[1] == col)
            rows = good_indices[0][col_indices]
            winds.ix[rows, ('x', rws_cols[col])] = xs[col_indices]
            winds.ix[rows, ('y', rws_cols[col])] = ys[col_indices]
            winds.ix[rows, ('z', rws_cols[col])] = zs[col_indices]

        windxr = xr.DataArray(winds).unstack('dim_1')
        self._obj['Windspeed'] = windxr
        self._obj['Windspeed'].attrs['units'] = 'm/s'
        return True

    def estimate_wind(self, method='Leosphere', **kwargs):
        if method=='Leosphere':
            self.estimate_wind_leosphere(**kwargs)
        elif method=='discrete':
            self.estimate_wind_discrete(**kwargs)
        else:
            pass

    def writeRAOB(self, time, filename, timedim='Time', temp='Temperature (K)', rh='Relative Humidity (%)',
                  vap_den=None, liq_wat=None, wind=True, wspeed=True, line_terminator='\n'):

        # set up the header information
        header_lines = []
        header_lines.append('RAOB/CSV, ' + 'Example Data from microwave radiometer and lidar')
        # header_lines.append('INFO:1, ' + 'First line of freeform text')
        # header_lines.append('INFO:2, ' + 'Another freeform text line')
        header_lines.append('DTG, ' + str(time))
        if 'latitude' in self._obj.attrs.keys(): header_lines.append('LAT, ' + str(self._obj.attrs['latitude']) + ', N')
        if 'longitude' in self._obj.attrs.keys(): header_lines.append('LON, ' + str(self._obj.attrs['longitude']) + ', W')
        if 'elevation' in self._obj.attrs.keys(): header_lines.append('ELEV, ' + str(self._obj.attrs['elevation']) + ', M')
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
        header_lines.append('RAOB/DATA' + line_terminator)
        header = line_terminator.join(header_lines)

        # set up the data (making sure to round as required)
        levels = self._obj.coords['Range'].values
        if wind:
            columns = ['PRES', 'TEMP', 'RH', 'UU', 'VV', 'GPM']
        else:
            columns = ['PRES', 'TEMP', 'RH', 'WIND', 'SPEED', 'GPM']
        df = pd.DataFrame(index=levels, columns=columns)
        df['TEMP'] = np.round(self._obj[temp].sel(**{timedim: time}), 1)
        df['RH'] = np.round(self._obj[rh].sel(**{timedim: time}), 1)
        # df['WIND'] = np.nan
        # df['SPEED'] = np.nan
        df['GPM'] = map(int, np.round(1000 * levels))
        df['PRES'] = np.round(1013.25 * np.exp(-df['GPM'] / 7000), 1)
        if vap_den is not None: df['VapDen'] = np.round(self._obj[vap_den].sel(**{timedim: time}), 3)
        if liq_wat is not None: df['LiqWat'] = np.round(self._obj[liq_wat].sel(**{timedim: time}), 3)
        #if self.wind is not None:
        if wind:
            df['UU'] = -np.round(self._obj['Windspeed'].sel(**{timedim: time, 'Component': 'y'}), 1)
            df['VV'] = -np.round(self._obj['Windspeed'].sel(**{timedim: time, 'Component': 'x'}), 1)
        if wspeed:
            df['WSPEED'] = -np.round(self._obj['Windspeed'].sel(**{timedim: time, 'Component': 'z'}), 1)

        # print(df)

        roab_file = open(filename, "w")
        roab_file.writelines(header)
        roab_file.close()
        # print(df.head())
        # exit()
        df.to_csv(filename, na_rep=-999, index=False, mode='a', line_terminator=line_terminator)

    # def recursive_resample(self, ds, rule, coord, dim, coords):
    #     if len(coords) == 0:
    #         return ds.swap_dims({dim: coord}).resample(rule, coord)
    #     else:
    #         arrays = []
    #         cur_coord = coords[0]
    #         next_coords = coords[1:]
    #         for coordn in ds.coords[cur_coord].values:
    #             ds2 = ds.sel(**{cur_coord: coordn})
    #             arrays.append(self.recursive_resample(ds2, rule, coord, dim, next_coords))
    #
    #         return xr.concat(arrays, ds.coords[cur_coord])

    def nd_resample(self, rule, coord, dim):
        coords = self._obj.coords[coord].coords.keys()
        coords.remove(coord)
        coords.remove(dim)
        return rasp.recursive_resample(self._obj, rule, coord, dim, coords)

    def split_dim(self, array, dim):
        ds = xr.Dataset()
        for value in self._obj.coords[dim].values:
            ds[value] = self._obj[array].sel(**{dim: value}).drop(dim)
        ds = xr.merge([self._obj, ds]).drop(array)
        # if inplace:
        #     self._obj = ds
        # else:
        #     return ds
        return ds


@xr.register_dataarray_accessor('rasp')
class RaspAccessor(object):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def plot_barbs(self, x=None, y=None, components=('x', 'y'), resample=None, ax=None):
        if resample is not None:
            l1 = self._obj.resample(resample, 'Timestamp')
        else:
            l1 = self._obj
        if x is None:
            x = 'Timestamp'
        if y is None:
            y = 'Range'
        xvals = [mdates.date2num(pd.Timestamp(val)) for val in l1.coords[x].values]
        yvals = l1.coords[y]
        X, Y = np.meshgrid(xvals, yvals)
        U = l1.sel(Component=components[0]).transpose()
        V = l1.sel(Component=components[1]).transpose()
        if ax is None:
            ax = plt.subplot(111)
        ax.barbs(X, Y, U, V)


# class ProfileTimeSeries(pd.DataFrame):
#     def __init__(self, *args, **kwargs):
#         # check that the index is datetimes, then init as a data frame
#         # if (not isinstance(df.index, pd.tseries.index.DatetimeIndex)):
#         #     raise ValueError('Data frame must be indexed by Datetimes')
#         #pd.DataFrame.__init__(self, df)
#         super(ProfileTimeSeries, self).__init__(*args, **kwargs)
#
#     # this is needed so that subsetting functions return a ProfileTimeSeries instead of a DataFrame
#     @property
#     def _constructor(self):
#         return ProfileTimeSeries
#
#     def plot_heatmap(self, ax, **kwargs):
#         # fix indices to plot the data with 'nearest' interpolation
#         index0 = self.index
#         new_index = index0[:-1] + (index0[1:] - index0[:-1]) / 2
#         new_index = new_index.insert(0, index0[0])
#         df = pd.DataFrame(self.as_matrix(), index = new_index, columns=self.columns, dtype='float')
#         df.loc[index0[-1],:] = np.nan
#
#         # set up graph
#         start_time = df.index[0]
#         end_time = df.index[-1]
#         xs = df.index.map(mdates.date2num)
#         ys = df.columns.map(float)
#         y2d, x2d = np.meshgrid(ys, xs)
#         ax.set_xlim(start_time, end_time)
#         m2 = np.ma.masked_invalid(df)
#         im = ax.pcolormesh(x2d, y2d, m2, **kwargs)
#         plt.colorbar(im)
#
#     def plot_profile(self, ax, legend=True, **kwargs):
#         kwargs['label'] = self.index
#         ys = self.columns.map(int)
#         ax.plot(self.transpose(), ys, **kwargs)
#         if legend:
#             # plt.legend(lines, self.index)
#             ax.legend(self.index)
