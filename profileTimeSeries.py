'''
This file uses the dataframe with time index
Main use is for plotting heatmaps using matplotlib
Includes the core functions handling the data
for plotting and aggregating by time
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class ProfileTimeSeries(pd.DataFrame):
    def plot_heatmap(self):
        xs0 = self.index
        mean_interval = sum((xs0[1:] - xs0[0:-1]).seconds) / (len(xs0) - 1)
        self.loc[self.index[-1] + pd.DateOffset(seconds=mean_interval)] = np.nan
        start_time = self.index[0]
        end_time = self.index[-1]
        xs = self.index.map(mdates.date2num)
        ys = self.columns.map(int)
        y2d, x2d = np.meshgrid(ys, xs)
        fig1 = plt.figure()
        ax = fig1.add_subplot(1, 1, 1)
        ax.set_xlim(start_time, end_time)
        ax.set_ylim(ys[0], ys[-1])
        im = ax.pcolormesh(x2d, y2d, self)
        plt.colorbar(im)
        # get rid of the extra row we added for plotting
        self.drop(self.index[-1], axis=0, inplace=True)