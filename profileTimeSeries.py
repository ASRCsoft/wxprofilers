'''
This file uses the dataframe with time index
Main use is for plotting heatmaps using matplotlib
Includes the core functions handling the data
for plotting and aggregating by time
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.dates as mdates
import copy


class ProfileTimeSeries(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        # check that the index is datetimes, then init as a data frame
        # if (not isinstance(df.index, pd.tseries.index.DatetimeIndex)):
        #     raise ValueError('Data frame must be indexed by Datetimes')
        #pd.DataFrame.__init__(self, df)
        super(ProfileTimeSeries, self).__init__(*args, **kwargs)

    # this is needed so that subsetting functions return a ProfileTimeSeries instead of a DataFrame
    @property
    def _constructor(self):
        return ProfileTimeSeries

    def plot_heatmap(self, ax, **kwargs):
        # fix indices to plot the data with 'nearest' interpolation
        index0 = self.index
        new_index = index0[:-1] + (index0[1:] - index0[:-1]) / 2
        new_index = new_index.insert(0, index0[0])
        df = pd.DataFrame(self.as_matrix(), index = new_index, columns=self.columns, dtype='float')
        df.loc[index0[-1],:] = np.nan

        # set up graph
        start_time = df.index[0]
        end_time = df.index[-1]
        xs = df.index.map(mdates.date2num)
        ys = df.columns.map(float)
        y2d, x2d = np.meshgrid(ys, xs)
        ax.set_xlim(start_time, end_time)
        m2 = np.ma.masked_invalid(df)
        im = ax.pcolormesh(x2d, y2d, m2, **kwargs)
        plt.colorbar(im)

    def plot_profile(self, ax, legend=True, **kwargs):
        kwargs['label'] = self.index
        ys = self.columns.map(int)
        ax.plot(self.transpose(), ys, **kwargs)
        if legend:
            # plt.legend(lines, self.index)
            ax.legend(self.index)
