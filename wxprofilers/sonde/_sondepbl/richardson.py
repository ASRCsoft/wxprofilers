'''Functions to calculate Bulk Richardson method PBL estimates.

Section numbers are from 'Planetary Boundary Layer (PBL) Height Value
Added Product (VAP): Radiosonde Retrievals' from the US Department of
Energy.

'''

from .utils import subsample_5mb, estimate_potential_temperature, celsius_to_kelvin, kelvin_to_celsius, find_first
import numpy as np

# Constants
g = 9.8 # gravitational constant
es1 = 6.11 # reference saturation vapor pressure
t1 = 273.15 # reference temperature
rv = 461.5 # gas constant for water vapor
llv = 1000 * 2256 # latent heat of vaporization
# ^ pretty sure this should be converted from kJ to J
epsilon = .622 # "ratio of the molecular weight of water vapor to the molecular weight of dry air"


def get_saturation_vapor_pressure(t):
    '''3.5, Eq. 12: saturation vapor pressure.

    `t` is temperature in Kelvin.'''
    return es1 * np.exp(-(llv / rv) * (1 / t - 1 / t1))

def get_partial_pressure_of_water_vapor(rh, t):
    '''3.5, Eq. 11: partial pressure of water vapor.

    `t` is temperature in Kelvin.'''
    es = get_saturation_vapor_pressure(t)
    return (rh / 100) * es

def get_virtual_temperature(p, rh, t):
    '''3.5, Eq. 10: virtual temperature.

    `t` is temperature in Celsius.'''
    # all of these temperatures should be in Kelvins
    tK = celsius_to_kelvin(t)
    e = get_partial_pressure_of_water_vapor(rh, tK)
    tvK = tK / (1 - (e / p) * (1 - epsilon))
    # convert back to celsius to be consistent with input data
    return kelvin_to_celsius(tvK)

def get_virtual_potential_temperature(p, rh, t):
    '''3.5, Eq. 9: virtual potential temperature.

    `t` is temperature in Celsius.'''
    # this is the same as section 3.1 eq. 1 (potential temperature),
    # just substituting virtual temperature for temperature
    tv = get_virtual_temperature(p, rh, t)
    return estimate_potential_temperature(tv, p)

def get_bulk_richardson_number(z, p, rh, t, u, v):
    '''3.5, Eq. 8: bulk Richardson number.'''
    p0 = p[0]
    rh0 = rh.iloc[0]
    t0 = t.iloc[0]
    theta_v0 = get_virtual_potential_temperature(p0, rh0, t0)
    theta_vz = get_virtual_potential_temperature(p, rh, t)
    # I think height should be height in meters, to match g, u, and v ???
    zm = 1000 * z
    return (g * zm / theta_v0) * ((theta_vz - theta_v0) / (u ** 2 + v ** 2))

def bulk_richardson_pbl(df, threshold=.25):
    '''3.5: Bulk Richardson PBL Height Method.'''
    df5mb = subsample_5mb(df)
    df5mb['ri_b'] = get_bulk_richardson_number(df5mb['Height'], df5mb.index,
                                               df5mb['RH'], df5mb['Temp'],
                                               df5mb['U'], df5mb['V'])
    # find index where Ri_b exceeds the threshold value
    reaches_threshold = find_first(df5mb['ri_b'] >= threshold)
    if reaches_threshold is None:
        return None
    return df5mb.iloc[reaches_threshold]['Height']
