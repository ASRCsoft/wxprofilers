import numpy as np
import pandas as pd
import profileTimeSeries as pts
import windProfiles as wind
import profileInstrument as pri
import math
import misc
#import copy

class Lidar(pri.ProfileInstrument):
    def __init__(self, tsdict,  profiles=None, location=None, scan=None, wind=None):
        # tsdict should be a MultiIndex ProfileTimeSeries
        self.data = tsdict
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

        # # create the multiIndex ProfileTimeSeries
        # iterables = [['x', 'y', 'z'], self.data[rws].columns]
        # mult_index = pd.MultiIndex.from_product(iterables, names=['Component', 'Range [m]'])
        # wind = pts.ProfileTimeSeries(index=self.profiles.index, columns=mult_index)
        windcols = self.data[rws].columns
        x = pts.ProfileTimeSeries(index=self.profiles.index, columns=windcols, dtype='float')
        y = pts.ProfileTimeSeries(index=self.profiles.index, columns=windcols, dtype='float')
        z = pts.ProfileTimeSeries(index=self.profiles.index, columns=windcols, dtype='float')

        status_mat = self.data[status].as_matrix()
        is_good = (status_mat[0:-4,:] + status_mat[1:-3,:] + status_mat[2:-2,:] +
                   status_mat[3:-1,:] + status_mat[4:,:]) > 4.9

        # vectorize by column
        for col in range(0, self.data[rws].shape[1] - 1):
            print(col)
            # can I do this somehow?
            # is_good_col = is_good[:, col]
            # row_los = self.profiles['LOS ID'][4:][is_good_col]
            # los0 = self.data[rws].iloc[row - row_los, col]
            # los1 = self.data[rws].iloc[row - ((row_los + 4) % 5), col]
            # los2 = self.data[rws].iloc[row - ((row_los + 3) % 5), col]
            # los3 = self.data[rws].iloc[row - ((row_los + 2) % 5), col]
            # los4 = self.data[rws].iloc[row - ((row_los + 1) % 5), col]
            for row in range(4, self.data[rws].shape[0] - 1):
                if is_good[row - 4, col]:
                    row_los = self.profiles['LOS ID'][row - 4]
                    los0 = self.data[rws].iat[row - row_los, col]
                    los1 = self.data[rws].iat[row - ((row_los + 4) % 5), col]
                    los2 = self.data[rws].iat[row - ((row_los + 3) % 5), col]
                    los3 = self.data[rws].iat[row - ((row_los + 2) % 5), col]
                    los4 = self.data[rws].iat[row - ((row_los + 1) % 5), col]
                    x.iat[row, col] = -(los2 - los0) / (2 * math.cos(el))
                    y.iat[row, col] = -(los3 - los1) / (2 * math.cos(el))
                    z.iat[row, col] = (los0 + los1 + los2 + los3) * .789 / (4 * math.sin(el)) + los4 * .211

        self.wind = wind.WindProfiles(x, y, z)

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
        self.wind = wind.WindProfiles(wind_speed, wind_se)

    def estimate_wind(self, method='Leosphere', **kwargs):
        if method=='Leosphere':
            self.estimate_wind_leosphere(**kwargs)
        elif method=='discrete':
            return(self.estimate_wind_discrete(**kwargs))
        else:
            # raise error because other methods don't exist!
            pass
