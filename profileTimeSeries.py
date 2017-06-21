'''
Extensions of xarray Datasets and DataArrays
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import rasppy.misc as rasp
import rasppy.cape as cape

# rewriting as an xarray module, following the guidelines here:
# http://xarray.pydata.org/en/stable/internals.html#extending-xarray
import xarray as xr

@xr.register_dataset_accessor('rasp')
class ProfileDataset(object):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def estimate_wind_leosphere(self, rws='RWS', status='Status', los='LOS'):
        if (self._obj[status] is None or self._obj[rws] is None or los not in self._obj.coords.keys()):
            # raise an error
            pass

        # elevation
        el = float(self._obj.attrs['scan_elevation_angle_deg']) * np.pi / 180

        # Occasionally the lidar will 'skip a beat', that is, skip a
        # LOS for god only knows what reason. When this happens
        # Leosphere's code just uses the previous measurement from
        # that LOS. I'm going to re-jigger this rws matrix to acheive
        # the same thing, basically tricking my code into thinking the
        # LOS was not skipped at all.
        los_diff = self._obj.coords[los][1:].values - self._obj.coords[los][:-1].values
        skipped = np.logical_not(np.in1d(los_diff, [1, -4]))
        skipped = np.insert(skipped, 0, False)
        nskipped = np.sum(skipped)
        longer_shape = self._obj[rws].values.shape
        longer_shape = (longer_shape[0] + nskipped, longer_shape[1])
        rws_mat = np.full(longer_shape, np.nan, float)
        cum_skipped = np.cumsum(skipped)
        index_map = np.array(range(self._obj[rws].values.shape[0])) + cum_skipped
        #return self._obj[rws].values
        rws_mat[index_map] = self._obj[rws].values
        #return rws_mat
        which_skipped = np.where(skipped)[0]
        # return which_skipped
        for n, i in enumerate(which_skipped):
            rws_mat[i + n] = rws_mat[i - 5 + n]
        # return rws_mat

        # also need to re-jigger the status matrix a bit
        status_mat = np.full(longer_shape, np.nan, int)
        status_mat[index_map] = self._obj[status].values.astype(int)
        # return status_mat
        for n, i in enumerate(which_skipped):
            status_mat[i + n] = status_mat[i - 5 + n]
        # return status_mat
        # is_good = (status_mat[0:-4,:] + status_mat[1:-3,:] + status_mat[2:-2,:] +
        #            status_mat[3:-1,:] + status_mat[4:,:]) > 4.9
        is_good = np.stack([status_mat[0:-4,:], status_mat[1:-3,:], status_mat[2:-2,:],
                            status_mat[3:-1,:], status_mat[4:,:]]).all(axis=0)
        # return is_good

        good_indices = np.where(is_good)
        # add 4 columns for the 4 removed earlier
        good_indices = (good_indices[0] + 4, good_indices[1])
        los_ids = self._obj.coords[los].astype(int).values
        los_ids = np.insert(los_ids, which_skipped, los_ids[which_skipped - 1] + 1 % 5)
        # for i in which_skipped: # add the missing LOS IDs
        #     los_ids = np.insert(los_ids, i, los_ids[i - 1] + 1 % 5)
        row_los = los_ids[good_indices[0]]
        # return row_los
        rws_cols = self._obj.coords['Range'].values
        good_cols = rws_cols[good_indices[1]]




        # create a multiIndex data frame to hold the data
        iterables = [['x', 'y', 'z'], rws_cols]
        mult_index = pd.MultiIndex.from_product(iterables, names=['Component', 'Range'])
        time_index = self._obj.coords['Time'].to_index()
        for n, i in enumerate(which_skipped):
            time_index = time_index.insert(i + n, time_index[i - 1 + n] + pd.Timedelta('1us'))
        # return time_index
        winds = pd.DataFrame(index=time_index, columns=mult_index, dtype='float')
        rws_df = pd.DataFrame(rws_mat, index=time_index, columns=rws_cols)

        # get the corresponding LOS values for each wind estimate
        los0 = rws_df.lookup(rws_df.index[good_indices[0] - row_los], good_cols)
        los1 = rws_df.lookup(rws_df.index[good_indices[0] - ((row_los + 4) % 5)], good_cols)
        los2 = rws_df.lookup(rws_df.index[good_indices[0] - ((row_los + 3) % 5)], good_cols)
        los3 = rws_df.lookup(rws_df.index[good_indices[0] - ((row_los + 2) % 5)], good_cols)
        los4 = rws_df.lookup(rws_df.index[good_indices[0] - ((row_los + 1) % 5)], good_cols)
        
        # got these weights from a maximum likelihood calculation
        weight0to3 = np.sin(el) / (4 * np.sin(el) ** 2 + 1)
        weight4 = 1 / (4 * np.sin(el) ** 2 + 1)
        xs = (los0 - los2) / (2 * np.cos(el))
        ys = (los1 - los3) / (2 * np.cos(el))
        zs = weight0to3 * (los0 + los1 + los2 + los3) + weight4 * los4

        # put the results in the right place
        for col in range(self._obj[rws].shape[1]):
            col_indices = np.where(good_indices[1] == col)
            rows = good_indices[0][col_indices]
            # swapping x/y and negative to get American coordinates!!:
            winds.ix[rows, ('x', rws_cols[col])] = -ys[col_indices]
            winds.ix[rows, ('y', rws_cols[col])] = -xs[col_indices]
            winds.ix[rows, ('z', rws_cols[col])] = -zs[col_indices]

        windxr = xr.DataArray(winds.iloc[index_map]).unstack('dim_1')#.rename({'dim_0': 'profile'})
        return windxr

    def estimate_wind(self, method='Leosphere', **kwargs):
        if method=='Leosphere':
            return self.estimate_wind_leosphere(**kwargs)
        elif method=='discrete':
            self.estimate_wind_discrete(**kwargs)
        else:
            pass

    def _estimate_cape(self, hpascals='hpascals', temp='Temperature'):
        hpascals = self._obj.coords[hpascals].values
        tempK = self._obj[temp].values
        tempC = tempK - 273.15
        rel_hum = self._obj['Relative Humidity'].values
        dewpoints = tempK - ((100 - rel_hum) / 5) - 273.15
        return cape.getcape(nk=self._obj.dims['Range'], p_in=hpascals, t_in=tempC, td_in=dewpoints)[0]

    def estimate_cape(self, hpascals='hpascals', temp='Temperature'):
        ntimes = len(self._obj.coords['Time'].values)
        cape = [ self._obj.isel(**{'Time': t}).rasp._estimate_cape() for t in range(ntimes) ]
        return xr.DataArray(cape, {'Time': self._obj.coords['Time']})
        # self
        # hpascals = self._obj.coords['hpascals'].values
        # tempK = self._obj['Temperature'].values
        # tempC = tempK - 273.15
        # rel_hum = self._obj['Relative Humidity'].values
        # dewpoints = tempK - ((100 - rel_hum) / 5) - 273.15
        # return cape.getcape(nk=self._obj.dims['Range'], p_in=hpascals, t_in=tempC, td_in=dewpoints)[0]

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
        df['GPM'] = list(map(int, np.round(1000 * levels)))
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

    def nd_resample(self, rule, coord, dim, **kwargs):
        coords = list(self._obj.coords[coord].dims)
        coords.remove(dim)
        return rasp.recursive_resample(self._obj, rule, coord, dim, coords, **kwargs)

    def split_array(self, array, dim):
        ds = xr.Dataset()
        for value in self._obj.coords[dim].values:
            ds[value] = self._obj[array].sel(**{dim: value}).drop(dim)
        ds = xr.merge([self._obj, ds]).drop(array)
        return ds

    def los_format(self, replace_nat=True):
        # switch to LOS format and print the new xarray object
        lidar2 = self._obj.copy()
        lidar2['scan'] = ('Time', np.cumsum(lidar2['LOS ID'].values == 0))
        lidar2.set_coords('scan', inplace=True)
        lidar2 = lidar2.set_index(profile=['scan', 'LOS ID'])
        lidar2.coords['profile'] = ('Time', lidar2.coords['profile'].to_index())
        lidar2.swap_dims({'Time': 'profile'}, inplace=True)
        lidar2 = lidar2.unstack('profile')
        if replace_nat:
            lidar2.rasp.replace_nat()

        return lidar2

    def replace_nat(self, timedim='Time'):
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

    def nd_resample(self, rule, coord, dim):
        coords = list(self._obj.coords[coord].dims)
        coords.remove(dim)
        return rasp.recursive_resample(self._obj, rule, coord, dim, coords)

    def plot_barbs(self, x=None, y=None, components=('x', 'y'), resample=None, resampley=None, ax=None):
        if x is None:
            x = 'Time'
        if resample is not None:
            l1 = self._obj.resample(resample, x)
        else:
            l1 = self._obj
        if y is None:
            y = 'Range'
        if resampley is not None:
            maxy = l1.coords[y].max()
            nbreaks = int(maxy / resampley) + 2
            bins = np.array(range(nbreaks)) * [resampley]
            labels = (bins[1:] + bins[:-1]) / 2
            l1 = l1.groupby_bins(group=y, bins=bins, labels=labels).mean(dim=y)
            bin_name = y + '_bins'
            l1 = l1.rename({bin_name: y})
        xvals = [mdates.date2num(pd.Timestamp(val)) for val in l1.coords[x].values]
        yvals = l1.coords[y]
        X, Y = np.meshgrid(xvals, yvals)
        U = l1.sel(Component=components[0])
        V = l1.sel(Component=components[1])
        if len(U.dims) > 2:
            U = U.squeeze()
        if len(V.dims) > 2:
            V = V.squeeze()
        # there should only be two dimensions!
        assert len(U.dims) == 2
        assert len(V.dims) == 2
        # y values should be the first dimension
        if U.dims[0] != y:
            U = U.transpose()
        if V.dims[0] != y:
            V = V.transpose()
        new_axis = ax is None
        if new_axis:
            ax = plt.subplot(111)
            xtick_locator = mdates.AutoDateLocator()
            xtick_formatter = mdates.AutoDateFormatter(xtick_locator)
        ax.barbs(X, Y, U, V)
        if new_axis:
            ax.set_ylabel(y)
            ax.xaxis.set_major_locator(xtick_locator)
            ax.xaxis.set_major_formatter(xtick_formatter)

    def plot_profile(self, y=None, **kwargs):
        if y is None:
            dimname = self._obj.dims[0]
        else:
            dimname = y
        ys = self._obj[dimname].values
        xs = self._obj#.values#.transpose()
        if self._obj.dims[0] != dimname:
            dims_order = [dimname]
            for d in self._obj.dims:
                if d != dimname:
                    dims_order.append(d)
            xs = xs.transpose(*dims_order)
        plt.plot(xs, ys, **kwargs)
        plt.xlabel(self._obj.name)
        plt.ylabel(dimname)
        if len(xs.dims) > 1:
            dim2 = xs.dims[1]
            labels = [ dim2 + ' = ' + str(x) for x in xs.coords[dim2].values ]
            plt.legend(labels)
        # if legend:
        #     # plt.legend(lines, self.index)
        #     ax.legend(self.index)

    def _plot_profile(self, ax=None, **kwargs):
        fgr = xr.plot.FacetGrid(skewtdat, **kwargs)

    def remove_where(self, logarr, inplace=False):
        if inplace:
            self._obj.values = xr.DataArray(np.where(logarr, np.nan, self._obj))
        else:
            return xr.DataArray(np.where(logarr, np.nan, self._obj), dims=self._obj.dims)
