import numpy as np
import pandas as pd
import profileTimeSeries as pts
import windProfiles as wind
import profileInstrument as pri
import math
import misc
#import copy

class Lidar(pri.ProfileInstrument):
    def __init__(self, tsdict,  profiles=None, location=None, scan=None, wind=None, xarray=None):
        # tsdict should be a MultiIndex ProfileTimeSeries
        super(Lidar, self).__init__(tsdict, xarray=xarray)
        #self.data = tsdict
        self.profiles = profiles
        self.scan = scan
        self.location = location
        self.wind = wind

    def estimate_wind_leosphere(self, rws='RWS [m/s]', status='Status'):
        if (self.data[status] is None or self.data[rws] is None or
                    self.profiles is None or 'LOS ID' not in self.profiles.columns):
            # raise an error
            pass

        el = float(self.scan['elevation_angle_deg']) * math.pi / 180

        # create the multiIndex ProfileTimeSeries
        rws_cols = self.data[rws].columns
        iterables = [['x', 'y', 'z'], rws_cols]
        mult_index = pd.MultiIndex.from_product(iterables, names=['Component', 'Range [m]'])
        winds = pts.ProfileTimeSeries(index=self.profiles.index, columns=mult_index, dtype='float')

        status_mat = self.data[status].as_matrix()
        is_good = (status_mat[0:-4,:] + status_mat[1:-3,:] + status_mat[2:-2,:] +
                   status_mat[3:-1,:] + status_mat[4:,:]) > 4.9

        good_indices = np.where(is_good)
        # add 4 columns for the 4 removed earlier
        good_indices = (good_indices[0] + 4, good_indices[1])
        row_los = self.profiles['LOS ID'][good_indices[0]].values

        los0 = self.data[rws].lookup(self.data[rws].index[good_indices[0] - row_los], rws_cols[good_indices[1]])
        los1 = self.data[rws].lookup(self.data[rws].index[good_indices[0] - ((row_los + 4) % 5)], rws_cols[good_indices[1]])
        los2 = self.data[rws].lookup(self.data[rws].index[good_indices[0] - ((row_los + 3) % 5)], rws_cols[good_indices[1]])
        los3 = self.data[rws].lookup(self.data[rws].index[good_indices[0] - ((row_los + 2) % 5)], rws_cols[good_indices[1]])
        los4 = self.data[rws].lookup(self.data[rws].index[good_indices[0] - ((row_los + 1) % 5)], rws_cols[good_indices[1]])

        xs = -(los2 - los0) / (2 * math.cos(el))
        ys = -(los3 - los1) / (2 * math.cos(el))
        zs = (los0 + los1 + los2 + los3) * .789 / (4 * math.sin(el)) + los4 * .211

        # YAAAAAAAAAAAAAAAAAAAAAAAYYYYYYYYYYYYYYYY it works!!!!!!!!!!
        for col in range(self.data[rws].shape[1]):
            col_indices = np.where(good_indices[1] == col)
            rows = good_indices[0][col_indices]
            winds.ix[rows, ('x', rws_cols[col])] = xs[col_indices]
            winds.ix[rows, ('y', rws_cols[col])] = ys[col_indices]
            winds.ix[rows, ('z', rws_cols[col])] = zs[col_indices]

        self.wind = wind.WindProfiles(winds)

    def estimate_wind_discrete(self, rws='RWS [m/s]', status='Status', interval='5T', max_se=1):
        if (self.data[status] is None or self.data[rws] is None or
                    self.profiles is None or 'LOS ID' not in self.profiles.columns):
            # raise an error
            pass

        mult_index = pd.MultiIndex.from_tuples(list(zip(self.data[rws].index, self.profiles['LOS ID'])),
                                                names=['Timestamp', 'LOS ID'])
        rwsdf = pd.DataFrame(self.data[rws].as_matrix(), index=mult_index, columns=self.data[rws].columns)
        # replace status=0 values with NaN
        rwsdf.where(self.data[status], np.nan, inplace=True)

        el = float(self.scan['elevation_angle_deg']) * math.pi / 180

        wind_reg = lambda x: misc.wind_regression(x, el, max_se)
        winddf = rwsdf.groupby(pd.Grouper(freq=interval, level=0)).apply(wind_reg)
        winddf.columns = ['x', 'y', 'z', 'x', 'y', 'z']
        winddf.reset_index(inplace=True)
        wind_speed = winddf.iloc[:,0:5].pivot(index='Timestamp', columns='Range [m]')
        wind_se = winddf.iloc[:,[0,1,5,6,7]].pivot(index='Timestamp', columns='Range [m]')
        self.wind = wind.WindProfiles(wind_speed, wind_se, dtype='float')

    def estimate_wind(self, method='Leosphere', **kwargs):
        if method=='Leosphere':
            self.estimate_wind_leosphere(**kwargs)
        elif method=='discrete':
            return(self.estimate_wind_discrete(**kwargs))
        else:
            # raise error because other methods don't exist!
            pass
