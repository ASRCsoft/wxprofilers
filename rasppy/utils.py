# -*- coding: utf-8 -*-
"""Miscellaneous utility functions"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import statsmodels.api as sm

def wind_regression(wdf, elevation=75, max_se=1):
    ncols = wdf.shape[1]
    colnames = wdf.columns
    los = wdf.index.get_level_values('LOS ID')
    az = los * np.pi / 2
    el = np.repeat(np.pi * 75 / 180, len(los))
    el[los == 4] = np.pi / 2

    x = np.sin(az) * np.cos(el)
    y = np.cos(az) * np.cos(el)
    z = np.sin(el)
    xmat = np.array([x, y, z]).transpose()

    df_columns = ['x', 'y', 'z', 'xse', 'yse', 'zse']
    resultsdf = pd.DataFrame(index=colnames, columns=df_columns)

    for n in range(ncols):
        ymat = -np.array([wdf.iloc[:, n]]).transpose()

        # make sure there are enough lines of sight to get a real measurement of all variables:
        notnan = np.logical_not(np.isnan(ymat[:, 0]))
        uniq_los = los[notnan].unique()
        n_uniq_los = len(uniq_los)
        if n_uniq_los < 3:
            continue
        elif n_uniq_los == 3:
            if ((0 not in uniq_los and 2 not in uniq_los)
                or (1 not in uniq_los and 3 not in uniq_los)):
                continue

        # run the regression:
        model = sm.OLS(ymat, xmat, missing='drop')
        results = model.fit()
        coefs = results.params
        se = results.bse
        # if any(se == 0):
        #     print("statsmodels says standard error is zero-- that's not right!")
        #     print(len(los[notnan].unique()))
        #     exit()
        coefs[np.logical_or(se > max_se, np.logical_not(np.isfinite(se)))] = np.nan
        df_data = np.concatenate((coefs, results.bse))
        resultsdf.loc[colnames[n], :] = df_data

    return resultsdf


def recursive_resample(ds, rule, coord, dim, coords, **kwargs):
    if len(coords) == 0:
        return ds.swap_dims({dim: coord}).resample(rule, coord, **kwargs)
    else:
        arrays = []
        cur_coord = coords[0]
        next_coords = coords[1:]
        for coordn in ds.coords[cur_coord].values:
            ds2 = ds.sel(**{cur_coord: coordn})
            arrays.append(recursive_resample(ds2, rule, coord, dim, next_coords, **kwargs))

        return xr.concat(arrays, ds.coords[cur_coord])

def skewt(data, splots, ranges, temp=None, rel_hum=None, **kwargs):
    from metpy.plots import SkewT
    if temp is None:
        temp = 'Temperature'
    if rel_hum is None:
        rel_hum = 'Relative Humidity'
    # convert range (m) to hectopascals
    #hpascals = 1013.25 * np.exp(-data.coords['Range'] / 7)
    hpascals = 1013.25 * np.exp(-ranges / 7)
    # convert temperature from Kelvins to Celsius
    tempC = data[0] - 273.15
    # estimate dewpoint from relative humidity
    dewpoints = data[0] - ((100 - data[1]) / 5) - 273.15

    # get info about the current figure
    # fshape = plt.gcf().axes.shape
    # skew = SkewT(fig=plt.gcf(), subplot=(fshape[0], fshape[1], splots[0]))
    skew = SkewT(fig=plt.gcf(), subplot=splots[0])
    #plt.gca().axis('off')
    splots.pop(0)
    skew.plot(hpascals, tempC, 'r')
    skew.plot(hpascals, dewpoints, 'g')
    skew.plot_dry_adiabats()
    skew.plot_moist_adiabats()
    if data.shape[0] == 4:
        u = data[2]
        v = data[3]
        skew.plot_barbs(hpascals, u, v, xloc=.9)
    # skew.plot_mixing_lines()
    # skew.ax.set_ylim(1100, 200)
