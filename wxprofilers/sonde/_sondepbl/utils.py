'''Utility functions used for calculating PBL estimates.

Section numbers are from 'Planetary Boundary Layer (PBL) Height Value
Added Product (VAP): Radiosonde Retrievals' from the US Department of
Energy.'''

import yaml, datetime
import numpy as np
import pandas as pd


# Constants
r_over_cpd = .286


# IO
def replace_bad_yaml(s):
    '''Make messy strings compatible with yaml.'''
    return s.replace('\t', ' ').replace('#', 'number')

def get_metadata(csv_path):
    '''Get metadata from yaml-like text at the beginning of a sonde csv
    (.txt) file.

    '''
    with open(csv_path, 'r') as f:
        lines = f.readlines()
    yaml_cutoff = lines.index('\n')
    yaml_lines = lines[:yaml_cutoff]
    yaml_text = ''.join([ replace_bad_yaml(s) for s in yaml_lines ])
    return yaml.load(yaml_text)

def write_metadata(meta):
    '''Write release metadata to postgres.'''
    pass

def read_listos_csv(path, **kwargs):
    '''Read a listos sonde data file, returning a pandas data frame. Extra
    arguments are passed to `pandas.read_csv`.

    '''
    df = pd.read_csv(path, sep=';', skiprows=8, **kwargs)
    # remove units from column names
    return df.rename(columns={ s: s.split('[')[0] for s in df.columns })


# QC/QA
def check_sonde_quality(df):
    '''3.1: Quality control checks'''
    if df.shape[0] < 1:
        return False
    if df['Height'].max() < 1:
        return False
    if df['P'].max() < 200:
        return False
    first10secs = df.loc[df['t'] <= 10]
    if first10secs['Temp'].max() - first10secs['Temp'].min() > 30:
        return False
    if df['Temp'].max() > 50 or df['Temp'].min() < -90:
        return False
    first2pressure = df['P'][:2]
    if (np.isnan(first2pressure) | first2pressure < 0).any():
        return False
    return True

def remove_bad_values(df):
    '''3.6: Quality control flags / removing bad values.'''
    df.at[(df['Height'] < .05) & (df['WS'] > 33.5), 'WS'] = np.nan
    return df


# Subsampling
def subsample_5mb(df):
    '''3.1: Subsampling.'''
    # make pressure the index
    df = df.set_index('P')
    # groupby 5mb, get the first (lowest) entry in each group
    df5mb = df.groupby(lambda l: int(l / 5) * 5).first()
    df5mb.index.name = 'P'
    return df5mb.sort_values('P', ascending=False)


# Physical/atmospheric calculations
def celsius_to_kelvin(t):
    '''Convert Celsius to Kelvin.'''
    return t + 273.15

def kelvin_to_celsius(t):
    '''Convert Kelvin to Celsius.'''
    return t - 273.15

def estimate_potential_temperature(t, p, p0=1000):
    '''3.1, Eq. 1: Potential temperature.

    `t` is temperature in degrees Celsius.

    Returns potential temperature in degrees Kelvin.'''
    tK = celsius_to_kelvin(t)
    return tK * (p0 / p) ** r_over_cpd


# useful stuff
def find_first(a):
    '''Find the index of the first true value in an array of boolean
    values.'''
    trues = np.where(a)[0]
    if len(trues) == 0:
        return None
    else:
        return trues[0]
