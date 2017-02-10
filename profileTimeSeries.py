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

    def plot_heatmap(self, **kwargs):
        xs0 = self.index
        mean_interval = sum((xs0[1:] - xs0[0:-1]).seconds) / (len(xs0) - 1)
        # add extra row to get the plot to get all the data to display correctly
        # print(self.index[-1])
        # print(pd.DateOffset(seconds=mean_interval))
        self.loc[self.index[-1] + pd.DateOffset(seconds=mean_interval),:] = np.nan
        start_time = self.index[0]
        end_time = self.index[-1]
        xs = self.index.map(mdates.date2num)
        ys = self.columns.map(int)
        y2d, x2d = np.meshgrid(ys, xs)
        fig1 = plt.figure()
        ax = fig1.add_subplot(1, 1, 1)
        ax.set_xlim(start_time, end_time)
        im = ax.pcolormesh(x2d, y2d, np.ma.masked_where(np.isnan(self), self), **kwargs)
        plt.colorbar(im)
        # get rid of the extra row we added for plotting
        self.drop(self.index[-1], axis=0, inplace=True)

    def plot_profile(self, ax, legend=True, **kwargs):
        kwargs['label'] = self.index
        ys = self.columns.map(int)
        ax.plot(self.transpose(), ys, **kwargs)
        if legend:
            # plt.legend(lines, self.index)
            ax.legend(self.index)
