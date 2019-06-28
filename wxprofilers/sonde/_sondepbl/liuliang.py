'''Functions to calculate Liu-Liang method PBL estimates.

Section numbers are from 'Planetary Boundary Layer (PBL) Height Value
Added Product (VAP): Radiosonde Retrievals' from the US Department of
Energy.'''

from .utils import subsample_5mb, estimate_potential_temperature, find_first
import numpy as np


# Constants
delta_s_land = 1 # inversion_strength_threshold
delta_s_water = .2
delta_u_land = .5 # instability_threshold
delta_u_water = .1
theta_r_land = 4 # overshoot_threshold
theta_r_water = 5


def layer_type(ptemps, land):
    '''3.2: Determine boundary layer type.

    `ptemps` are potential temperatures subsampled at 5mb intervals.'''
    if land:
        delta_s = delta_s_land
    else:
        delta_s = delta_s_water
    ptemp2 = ptemps.iloc[1]
    ptemp5 = ptemps.iloc[4]
    if ptemp5 - ptemp2 < -delta_s:
        return 'CBL'
    elif ptemp5 - ptemp2 > delta_s:
        return 'SBL'
    else:
        return 'NRL'

def get_stability_pbl_index(df, theta_r):
    '''3.3.2, Eq. 7: PBL height based on a stability criteria.'''
    # first find lowest local minimum
    # local minimums happen where derivative changes from negative to positive
    dthetak = df['ptemp'].diff() / df['Height'].diff()
    lowest_min = find_first((dthetak < 0) & (dthetak.shift(-1) > 0))
    if lowest_min is None:
        return None

    # test conditions (eq. 7)
    is_local_peak = dthetak.iloc[lowest_min] - dthetak.iloc[lowest_min - 1] < -40
    below_inversion_layer = ((dthetak.iloc[lowest_min + 1] < theta_r) &
                             (dthetak.iloc[lowest_min + 2] < theta_r))
    meets_stability_criteria = is_local_peak or below_inversion_layer
    if meets_stability_criteria:
        return lowest_min
    else:
        return None

def get_wind_shear_pbl_index(ws):
    '''3.3.2: PBL height based on a wind shear criteria.'''
    # look for a low-level jet
    nose = ws.values.argmax()
    if nose == ws.shape[0] - 1:
        # the potential nose is at the top of the measured data and
        # therefore we can't test to see if it's actually a nose
        strong_nose = False
    else:
        strong_nose = ((ws.iloc[nose] - ws.iloc[nose - 1] > 2) &
                       (ws.iloc[nose] - ws.iloc[nose + 1] > 2))
    ws_decreases_monotonically = (ws.iloc[:nose].diff() >= 0).all()
    meets_wind_shear_criteria = strong_nose and ws_decreases_monotonically
    if meets_wind_shear_criteria:
        return nose
    else:
        return None

def liu_liang_stable(df, theta_r):
    '''3.3.2: Liu-Liang estimate of boundary layer in stable regimes.

    `df` should be the sonde data subsampled at 5mb intervals.'''
    stability_pbl = get_stability_pbl_index(df, theta_r)
    wind_shear_pbl = get_wind_shear_pbl_index(df['WS'])
    if stability_pbl is not None and wind_shear_pbl is not None:
        return df.iloc[min(stability_pbl, wind_shear_pbl)]['Height']
    elif stability_pbl is not None:
        return df.iloc[stability_pbl]['Height']
    elif wind_shear_pbl is not None:
        return df.iloc[wind_shear_pbl]['Height']
    else:
        return np.nan

def get_lowest_rising_adiabatic_air_parcel_index(ptemps, delta_u):
    '''3.3.1, Eq. 5: lowest rising adiabatic air parcel.'''
    theta_k_minus_theta_1 = ptemps - ptemps.iloc[0]
    return find_first(theta_k_minus_theta_1 > delta_u)

def get_ptemp_gradient_reaches_overshoot_threshold_index(df, theta_r):
    '''3.3.1, Eq. 6: the lowest level where the potential temperature
    gradient with height is greater than the overshooting threshold of
    the rising parcel.

    '''
    dtheta_k = df['ptemp'].diff() / df['Height'].diff()
    return find_first(dtheta_k > theta_r)

def liu_liang_unstable(df, delta_u, theta_r):
    '''3.3.1: Liu-Liang estimate of boundary layer in unstable regimes.

    `df` should be the sonde data subsampled at 5mb intervals.'''
    k5 = get_lowest_rising_adiabatic_air_parcel_index(df['ptemp'], delta_u)
    # ^ this is k from equation 5
    dfk5 = df.iloc[k5:]
    k6 = get_ptemp_gradient_reaches_overshoot_threshold_index(dfk5, theta_r)
    # ^ this is the k from equation 6
    if k6 is None:
        return np.nan
    else:
        return dfk5.iloc[k6]['Height']
    
def liu_liang_pbl(df, land=True):
    '''3.3: Liu-Liang PBL Height Method'''
    df5mb = subsample_5mb(df)
    df5mb['ptemp'] = estimate_potential_temperature(df5mb['Temp'], df5mb.index)
    regime = layer_type(df5mb['ptemp'], land)
    stable = regime == 'SBL'
    if land:
        delta_u = delta_u_land
        theta_r = theta_r_land
    else:
        delta_u = delta_u_water
        theta_r = theta_r_water
    if stable:
        return liu_liang_stable(df5mb, theta_r)
    else:
        return liu_liang_unstable(df5mb, delta_u, theta_r)
