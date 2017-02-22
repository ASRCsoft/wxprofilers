import numpy as np
import profileTimeSeries as pts
import matplotlib.dates as mdates


class WindProfiles:
    def __init__(self, speed, standard_error=None, **kwargs):
        self.speed = pts.ProfileTimeSeries(speed, **kwargs)
        if standard_error is not None:
            self.standard_error = pts.ProfileTimeSeries(standard_error, **kwargs)


    def plot_barbs(self, ax, **kwargs):
        # needs a little work
        if self.speed['x'] is None or self.speed['y'] is None:
            # raise an error
            pass
        xs = self.speed['x'].index.map(mdates.date2num)
        print(xs[0])
        print(xs[-1])
        #xs = (xs - xs.min()) / (xs.max() - xs.min()) + 1000000
        ys = self.speed['x'].columns.map(float)
        X, Y = np.meshgrid(xs, ys)
        # #ax.set_xlim(xs[0], xs[-1])
        # xmat = np.ma.masked_invalid(self.speed['x'].as_matrix())
        # ymat = np.ma.masked_invalid(self.speed['y'].as_matrix())
        ax.barbs(X, Y, self.speed['x'].transpose(), self.speed['y'].transpose(), **kwargs)
        #ax.set_xlim(self.speed['x'].index[0], self.speed['x'].index[-1])
