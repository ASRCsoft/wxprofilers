'''Functions to calculate Heffter method PBL estimates.

Section numbers are from 'Planetary Boundary Layer (PBL) Height Value
Added Product (VAP): Radiosonde Retrievals' from the US Department of
Energy.'''

from .utils import subsample_5mb, estimate_potential_temperature, find_first
import numpy as np


# Constants
lapse_rate_threshold = .005


def subsample_15mb(df):
    '''3.4'''
    return subsample_5mb(df).rolling(3).mean()

def lapse_rate(ptemp, h):
    '''Calculate potential temperature lapse rates, reported in K/m.

    uh... not sure if this should be positive or negative... positive
    seems to work best.

    '''
    return ptemp.diff() / (1000 * h.diff())

def is_inversion(ptemp, h):
    '''A boolean value indicating inversion layers.'''
    return lapse_rate(ptemp, h) > lapse_rate_threshold

def find_inversion_limits(ptemp, h):
    '''Return an array with the top and bottom inversion indices.'''
    inversion = is_inversion(ptemp, h)
    inversion_bottom = ~inversion & inversion.shift(-1)
    inversion_top = inversion & ~inversion.shift(-1).fillna(False)
    return np.array([np.where(inversion_bottom)[0],
                     np.where(inversion_top)[0]])

def inversion_ptemp_diffs(ptemps, inv_limits):
    '''Get the potential temperature differences for a set of temperature
    inversion limits.

    '''
    limit_temps = ptemps.iloc[inv_limits.flatten()].values.reshape(inv_limits.shape)
    diffs = limit_temps[1] - limit_temps[0]
    return diffs

def heffter_pbl(df):
    '''3.4: Heffter PBL Height Method.'''
    df15mb = subsample_15mb(df)
    # find inversions with potential temperature differences greater
    # than 2 degrees Celsius
    df15mb['ptemp'] =  estimate_potential_temperature(df15mb['Temp'], df15mb.index)
    inv_limits = find_inversion_limits(df15mb['ptemp'], df15mb['Height'])
    inv_diffs = inversion_ptemp_diffs(df15mb['ptemp'], inv_limits)
    diff_gt2 = find_first(inv_diffs > 2)
    if diff_gt2 is not None:
        # get the first matching inversion
        first_inv_gt2 = inv_limits[:, diff_gt2]
        # find the first level with ptemp > first_ptemp + 2
        inversion_df = df15mb.iloc[first_inv_gt2[0]:first_inv_gt2[1] + 1]
        first_ptemp = inversion_df.iloc[0]['ptemp']
        pbl_ind = find_first(inversion_df['ptemp'] > first_ptemp + 2)
        # return the bottom
        return inversion_df.iloc[pbl_ind]['Height']
    else:
        # get the maximum potential temperature gradient
        d_ptemp = df15mb['ptemp'].diff() / df15mb['Height'].diff()
        return df15mb.index[d_ptemp.values.argmax()]
