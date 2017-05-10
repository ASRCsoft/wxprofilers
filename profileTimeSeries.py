'''
Extensions of xarray Datasets and DataArrays
'''
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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

        el = float(self._obj.attrs['elevation_angle_deg']) * math.pi / 180

        # create the multiIndex ProfileTimeSeries
        #rws_cols = self.data[rws].columns
        rws_cols = self._obj.coords['Range'].values
        iterables = [['x', 'y', 'z'], rws_cols]
        mult_index = pd.MultiIndex.from_product(iterables, names=['Component', 'Range'])
        winds = pd.DataFrame(index=self._obj.coords['Timestamp'].to_index(), columns=mult_index, dtype='float')

        #status_mat = self.data[status].as_matrix()
        status_mat = self._obj[status].values.astype(int)
        is_good = (status_mat[0:-4,:] + status_mat[1:-3,:] + status_mat[2:-2,:] +
                   status_mat[3:-1,:] + status_mat[4:,:]) > 4.9

        good_indices = np.where(is_good)
        # add 4 columns for the 4 removed earlier
        good_indices = (good_indices[0] + 4, good_indices[1])
        row_los = self._obj.coords['LOS ID'][good_indices[0]].astype(int).values
        #return row_los

        rws_mat = pd.DataFrame(self._obj[rws].values, index=self._obj.coords['Timestamp'].to_index(), columns=rws_cols)
        good_cols = rws_cols[good_indices[1]]
        los0 = rws_mat.lookup(rws_mat.index[good_indices[0] - row_los], good_cols)
        los1 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 4) % 5)], good_cols)
        los2 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 3) % 5)], good_cols)
        los3 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 2) % 5)], good_cols)
        los4 = rws_mat.lookup(rws_mat.index[good_indices[0] - ((row_los + 1) % 5)], good_cols)

        # these numbers are weird but should match the Lidar (but
        xs = (los0 - los2) / (2 * math.cos(el))
        ys = (los1 - los3) / (2 * math.cos(el))
        zs = (los0 + los1 + los2 + los3) * .789 / (4 * math.sin(el)) + los4 * .211

        # YAAAAAAAAAAAAAAAAAAAAAAAYYYYYYYYYYYYYYYY it works!!!!!!!!!!
        for col in range(self._obj[rws].shape[1]):
            col_indices = np.where(good_indices[1] == col)
            rows = good_indices[0][col_indices]
            # swapping x/y and negative to get American coordinates!!:
            winds.ix[rows, ('x', rws_cols[col])] = -ys[col_indices]
            winds.ix[rows, ('y', rws_cols[col])] = -xs[col_indices]
            winds.ix[rows, ('z', rws_cols[col])] = -zs[col_indices]

        windxr = xr.DataArray(winds).unstack('dim_1')#.rename({'dim_0': 'profile'})
        #return windxr
        range_attrs = self._obj.coords['Range'].attrs
        self._obj['Windspeed'] = windxr
        self._obj.coords['Range'].attrs = range_attrs
        self._obj['Windspeed'].attrs['units'] = 'm/s'
        return True

    def estimate_wind(self, method='Leosphere', **kwargs):
        if method=='Leosphere':
            return self.estimate_wind_leosphere(**kwargs)
        elif method=='discrete':
            self.estimate_wind_discrete(**kwargs)
        else:
            pass

    def write_raob(self, time, filename, timedim='Time', temp='Temperature', rh='Relative Humidity',
                  vap_den=None, liq_wat=None, wind=True, wspeed=True, line_terminator='\n'):

        # set up the header information
        header_lines = []
        #header_lines.append('RAOB/CSV, ' + 'Example Data from microwave radiometer and lidar')
        #time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        time_str = pd.to_datetime(time).strftime('%Y-%m-%d %H:%M:%S')
        header_lines.append('RAOB/CSV, ' + time_str)
        # header_lines.append('INFO:1, ' + 'First line of freeform text')
        # header_lines.append('INFO:2, ' + 'Another freeform text line')
        header_lines.append('DTG, ' + time_str)
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
            df['UU'] = np.round(self._obj['Windspeed'].sel(**{timedim: time, 'Component': 'x'}), 1)
            df['VV'] = np.round(self._obj['Windspeed'].sel(**{timedim: time, 'Component': 'y'}), 1)
        if wspeed:
            df['WSPEED'] = np.round(self._obj['Windspeed'].sel(**{timedim: time, 'Component': 'z'}), 1)

        # print(df)

        roab_file = open(filename, "w")
        roab_file.writelines(header)
        roab_file.close()
        # print(df.head())
        # exit()
        df.to_csv(filename, na_rep=-999, index=False, mode='a', line_terminator=line_terminator)

    def nd_resample(self, rule, coord, dim):
        coords = list(self._obj.coords[coord].dims)
        coords.remove(dim)
        return rasp.recursive_resample(self._obj, rule, coord, dim, coords)

    def split_array(self, array, dim):
        ds = xr.Dataset()
        for value in self._obj.coords[dim].values:
            ds[value] = self._obj[array].sel(**{dim: value}).drop(dim)
        ds = xr.merge([self._obj, ds]).drop(array)
        return ds

    def los_format(self, replace_nat=True):
        # switch to LOS format and print the new xarray object
        lidar2 = self._obj.copy()
        lidar2['scan'] = ('Timestamp', np.cumsum(lidar2['LOS ID'].values == 0))
        lidar2.set_coords('scan', inplace=True)
        lidar2 = lidar2.set_index(profile=['scan', 'LOS ID'])
        lidar2.coords['profile'] = ('Timestamp', lidar2.coords['profile'].to_index())
        lidar2.swap_dims({'Timestamp': 'profile'}, inplace=True)
        lidar2 = lidar2.unstack('profile')
        if replace_nat:
            lidar2.rasp.replace_nat()

        return lidar2

    def replace_nat(self, timedim='Timestamp'):
        max_los = self._obj.coords['LOS ID'].max()
        # get all missing except for the last scan
        missing = np.where(pd.isnull(self._obj.coords[timedim][0:-1, :]))
        # replace missing times with the next time:
        for n in reversed(range(len(missing[0]))):
            # index contains scan, then LOS ID
            index = (missing[0][n], missing[1][n])
            if index[1] == max_los:
                next_index = (index[0] + 1, 0)
            else:
                next_index = (index[0], index[1] + 1)
            next_time = self._obj.coords[timedim].values[next_index[0], next_index[1]]
            if not pd.isnull(next_time):
                self._obj.coords[timedim][index[0], index[1]] = next_time

        # this will leave some times still missing at the end
        # fix the remaining missing times by replacing them with the previous time:
        missing = np.where(pd.isnull(self._obj.coords[timedim]))
        for n in range(len(missing[0])):
            index = (missing[0][n], missing[1][n])
            if index[1] == 0:
                prev_index = (index[0] - 1, max_los)
            else:
                prev_index = (index[0], index[1] - 1)
            prev_time = self._obj.coords[timedim].values[prev_index[0], prev_index[1]]
            if not pd.isnull(prev_time):
                self._obj.coords[timedim][index[0], index[1]] = prev_time

    def remove_where(self, arrays, logarr):
        for array in arrays:
            self._obj[array].values = np.where(logarr, np.nan, self._obj[array])

    def skewt(self, ranges='Range', temp='Temperature', dewpoint=None, rel_hum='Relative Humidity',
              temp_units='K', wind=None, **kwargs):
        from metpy.plots import SkewT
        if not 'col' in kwargs.keys() and not 'row' in kwargs.keys():
            # get unused dimensions
            unused = list(self._obj[temp].dims)
            if ranges in unused:
                unused.remove(ranges)
            # convert range (m) to hectopascals
            hpascals = 1013.25 * np.exp(-self._obj.coords[ranges] / 7)
            # return hpascals
            #return hpascals
            # convert temperature from Kelvins to Celsius
            #tempC = self._obj[temp] - 273.15
            if temp_units == 'K':
                tempK = self._obj[temp].drop(unused)
                tempC = tempK - 273.15
            else:
                tempC = self._obj[temp].drop(unused)
                tempK = tempC + 273.15

            if dewpoint is None:
                # estimate dewpoint from relative humidity
                dewpoints = tempK - ((100 - self._obj[rel_hum].drop(unused)) / 5) - 273.15
            else:
                dewpoints = self._obj[dewpoint].drop(unused)

            skew = SkewT()
            #return tempC
            skew.plot(hpascals, tempC, 'r')
            skew.plot(hpascals, dewpoints, 'g')
            skew.plot_dry_adiabats()
            skew.plot_moist_adiabats()
            if not wind is None:
                u = self._obj[wind].sel(Component='x').drop(unused)
                v = self._obj[wind].sel(Component='y').drop(unused)
                skew.plot_barbs(hpascals, u, v, xloc=.9)
            # skew.plot_mixing_lines()
            # skew.ax.set_ylim(1100, 100)
        else:
            if not wind is None:
                skewtdat = xr.concat([self._obj['Temperature'], self._obj['Relative Humidity'],
                                      self._obj[wind].sel(Component='x').drop('Component'),
                                      self._obj[wind].sel(Component='y').drop('Component')],
                                     'measure')
                skewtdat.coords['measure'] = ['Temperature', 'Relative Humidity', 'windx', 'windy']
            else:
                skewtdat = xr.concat([self._obj['Temperature'], self._obj['Relative Humidity']], 'measure')
                skewtdat.coords['measure'] = ['Temperature', 'Relative Humidity']

            # skewtdat
            sk1 = xr.plot.FacetGrid(skewtdat, **kwargs)
            #return sk1
            # need to make the subplot tuples

            for ax in sk1.axes.flat:
                ax.axis('off')

            #return sk1.axes.flat
            #return len(sk1.axes.flat)
            splots = range(len(sk1.axes.flat))
            #return splots
            splot_dims = sk1.axes.shape
            splot_tuples = []
            for i in splots:
                splot_tuples.append((splot_dims[0], splot_dims[1], i + 1))

            if not wind is None:
                sk1.map(rasp.skewt, [0, 1, 2, 3], splots=splot_tuples, ranges=skewtdat.coords['Range'].values)
            else:
                sk1.map(rasp.skewt, [0, 1], splots=splot_tuples, ranges=skewtdat.coords['Range'].values)


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

    def remove_where(self, logarr, inplace=False):
        if inplace:
            self._obj.values = xr.DataArray(np.where(logarr, np.nan, self._obj))
        else:
            return xr.DataArray(np.where(logarr, np.nan, self._obj), dims=self._obj.dims)