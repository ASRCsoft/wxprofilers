'''
This file uses the dataframe with time index
Main use is for plotting heatmaps using matplotlib
Includes the core functions handling the data
for plotting and aggregating by time
'''
import pandas as pd
import matplotlib.pyplot as plt

class ProfileTimeSeries(pd.DataFrame):
    def plot_heatmap(self):
        xs0 = cnr.index
        mean_interval = sum((xs0[1:] - xs0[0:-1]).seconds) / (len(xs0) - 1)
        cnr.loc[cnr.index[-1] + pd.DateOffset(seconds=mean_interval)] = np.nan
        start_time = cnr.index[0]
        end_time = cnr.index[-1]
        xs = cnr.index.map(mdates.date2num)
        ys = cnr.columns.map(int)
        y2d, x2d = np.meshgrid(ys, xs)
        fig1 = plt.figure()
        ax = fig1.add_subplot(1, 1, 1)
        ax.set_xlim(start_time, end_time)
        ax.set_ylim(ys[0], ys[-1])
        im = ax.pcolormesh(x2d, y2d, cnr)
        plt.colorbar(im)