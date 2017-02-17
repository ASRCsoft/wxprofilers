import numpy as np
import profileTimeSeries as pts
import matplotlib.dates as mdates


class WindProfiles:
    def __init__(self, speed, standard_error=None):
        self.speed = pts.ProfileTimeSeries(speed)
        if standard_error is not None:
            self.standard_error = pts.ProfileTimeSeries(standard_error)


    def plot_barbs(self, ax):
        # needs a little work
        if self.speed['x'] is None or self.speed['y'] is None:
            # raise an error
            pass
        xs = self.speed['x'].index.map(mdates.date2num)
        print(xs[0])
        print(xs[-1])
        #xs = (xs - xs.min()) / (xs.max() - xs.min()) + 1000000
        ys = self.speed['x'].columns.map(int)
        X, Y = np.meshgrid(xs, ys)
        #ax.set_xlim(xs[0], xs[-1])
        ax.barbs(X, Y, self.speed['x'], self.speed['y'])
        ax.set_xlim(self.speed['x'].index[0], self.speed['x'].index[-1])
