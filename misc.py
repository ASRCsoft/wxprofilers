# -*- coding: UTF-8 -*-
import xml.etree.ElementTree
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import profileTimeSeries as pts
import math
import io
import re
import statsmodels.api as sm


def lidar_from_csv(rws, scans=None, location=None, scan_id=None, lidar=None, loc=None):
    # create a lidar object from Nathan's csv files
    csv = pd.read_csv(rws)

    # organize the data
    profile_vars = ['LOS ID', 'Configuration ID', 'Azimuth [°]', 'Elevation [°]']
    data = csv.drop(profile_vars, 1).pivot(index='Timestamp', columns='Range [m]')
    data.index = pd.to_datetime(data.index)

    # get the individual profiles
    #profiles = csv[['Timestamp', 'LOS ID']].drop_duplicates()
    #profiles.index = pd.DatetimeIndex(profiles['Timestamp'])

    # these fields will be variables in the xarray object
    # remove columns that don't exist in the csv file (for example, if not using the whole radial wind data)
    measurement_vars = ['RWS [m/s]', 'DRWS [m/s]', 'CNR [db]', 'Confidence Index [%]', 'Mean Error', 'Status']
    measurement_vars = list(set(measurement_vars) & set(csv.columns))

    # get profile-specific variables
    profile_vars.append('Timestamp')
    csv_profs = csv[profile_vars].groupby('Timestamp').agg(lambda x: x.iloc[0])

    h1 = {}
    coords = {'Timestamp': ('Timestamp', data.index), 'Range [m]': data.columns.levels[1]}
    if lidar is not None:
        coords['Lidar'] = [lidar]
        if loc is not None:
            coords['latitude'] = ('Lidar', [loc[0]])
            coords['longitude'] = ('Lidar', [loc[1]])
    profile_vars.remove('Timestamp')  # get rid of 'Timestamp'

    # get the scan info
    if scans is not None:
        scan_xml = xml.etree.ElementTree.parse(scans).getroot()
        # in real life, we should search for the scan with the given id (if one is given) and get the info for that scan
        scan_info = scan_xml[0][1][2][0].attrib
        # add the prefix 'scan_' to all the

    else:
        scan = None


    for scan_type in profile_vars:
        coords[scan_type] = ('Timestamp', csv_profs[scan_type])
    for level in measurement_vars:
        h1[level] = (('Timestamp', 'Range [m]'), xr.DataArray(data[level]))

    xarray = xr.Dataset(h1, coords=coords, attrs=scan_info)
    xarray.rename({'RWS [m/s]': 'RWS', 'DRWS [m/s]': 'DRWS', 'CNR [db]': 'CNR', 'Range [m]': 'Range',
                   'Azimuth [°]': 'Azimuth', 'Elevation [°]': 'Elevation'}, inplace=True)

    # set the units
    xarray['RWS'].attrs['units'] = 'm/s'
    xarray['DRWS'].attrs['units'] = 'm/s'
    xarray['CNR'].attrs['units'] = 'dB'
    xarray.coords['Range'].attrs['units'] = 'm'
    xarray.coords['Azimuth'].attrs['units'] = 'degrees'
    xarray.coords['Elevation'].attrs['units'] = 'degrees'

    if 'Confidence Index [%]' in measurement_vars:
        xarray.rename({'Confidence Index [%]': 'Confidence Index'}, inplace=True)
        xarray['Confidence Index'].attrs['units'] = 'percent'

    if 'Status' in measurement_vars:
        xarray['Status'] = xarray['Status'].astype(bool)

    return xarray


def mr_from_csv(file, scan='Zenith', resample=None, mrname=None, **kwargs):
    # read file
    f = open(file, "r")
    lines = f.readlines()
    f.close()

    # get the type of each line
    types = [int(re.sub(",.*", "", re.sub("^[^,]*,[^,]*,", "", line))) for line in lines]
    headers = np.where([re.search("^Record", line) for line in lines])

    # organize into csv's
    csvs = {}
    for n in np.nditer(headers):
        acceptable_types = np.array([1, 2, 3, 4])
        acceptable_types += types[n]
        is_type = [types[m] in acceptable_types for m in range(len(types))]
        where_is_type = np.where(is_type)
        if where_is_type[0].size > 0:
            csv_lines = [lines[m] for m in np.nditer(where_is_type)]
            csv_lines.insert(0, lines[n])
            csv_string = ''.join(csv_lines)
            csv = io.StringIO(csv_string.decode('utf-8'))
            df = pd.read_csv(csv)
            csvs[str(types[n])] = df

    record_types = csvs['100']['Title'].values
    names = [ re.split(' \(', record_type)[0] for record_type in record_types ]
    units = [ re.sub('.*\(|\).*', '', record_type) for record_type in record_types ]
    record_unit_dict = {}
    for n in range(len(record_types)):
        record_unit_dict[names[n]] = units[n]

    mr_data = {}

    csvs['400']['DataQuality'] = csvs['400']['DataQuality'].astype(bool)
    df400 = csvs['400']
    df400['Date/Time'] = pd.to_datetime(df400['Date/Time'])
    for n in range(csvs['100'].shape[0]):
        name = names[n]
        is_type = np.logical_and(df400['400'] == csvs['100']['Record Type'][n],
                                 df400['LV2 Processor'] == scan)
        df = df400.loc[is_type, df400.columns[4:-1]]
        df.index = df400.loc[is_type, 'Date/Time']
        df.columns = df.columns.map(float)
        mr_data[name] = df

    # convert data frame to xarray
    mrdf = df400
    # add a scan number (like record number, but for all measurements together)
    mrdf['scan'] = np.floor_divide(range(mrdf.shape[0]), 16)
    mrdf.set_index(['scan', '400', 'LV2 Processor'], inplace=True)
    mrdf2 = mrdf.drop(['Record', 'DataQuality', 'Date/Time'], axis=1)
    mrxr = xr.DataArray(mrdf2).unstack('dim_0')
    mrtimes = xr.DataArray(mrdf['Date/Time']).unstack('dim_0')
    mrds = xr.Dataset({'Measurement': mrxr, 'Date/Time': mrtimes})
    mrds['DataQuality'] = xr.DataArray(mrdf['DataQuality']).unstack('dim_0')
    mrds.coords['dim_1'] = mrxr.coords['dim_1'].values.astype(float)
    mrds.rename({'400': 'Record Type', 'dim_1': 'Range'}, inplace=True)
    mrds.coords['Record Type'] = names
    mrds.coords['Range'].attrs['units'] = 'km'
    mrds['Measurement'].attrs['units'] = record_unit_dict
    mrds.set_coords('Date/Time', inplace=True)

    if mrname is not None:
        mrds = mrds.expand_dims('Radiometer')
        mrds.coords['Radiometer'] = [mrname]
        # loc=None
        # if loc is not None:
        #     mrds.coords['latitude'] = ('lidar', [loc[0]])
        #     mrds.coords['longitude'] = ('lidar', [loc[1]])

    if resample is None:
        return mrds
    else:
        return mrds.rasp.nd_resample('5T', 'Date/Time', 'scan').rasp.split_array('Measurement', 'Record Type')


def wind_regression(wdf, elevation=75, max_se=1):
    ncols = wdf.shape[1]
    colnames = wdf.columns
    los = wdf.index.get_level_values('LOS ID')
    az = los * math.pi / 2
    el = np.repeat(math.pi * 75 / 180, len(los))
    el[los == 4] = math.pi / 2

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


def recursive_resample(ds, rule, coord, dim, coords):
    if len(coords) == 0:
        return ds.swap_dims({dim: coord}).resample(rule, coord)
    else:
        arrays = []
        cur_coord = coords[0]
        next_coords = coords[1:]
        for coordn in ds.coords[cur_coord].values:
            ds2 = ds.sel(**{cur_coord: coordn})
            arrays.append(recursive_resample(ds2, rule, coord, dim, next_coords))

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

def weather_balloon(fname):
    # get metadata
    fo = open(fname, 'r')
    lines = fo.readlines()
    fo.close()
    # header_end = np.where(np.equal(lines, '\r\n'))
    header_end = np.where([line == '\r\n' for line in lines])[0][0]
    lines = lines[0:header_end]
    lines = [line.strip() for line in lines]
    metadata = {}
    for line in lines:
        parts = line.split(' : ')
        key = parts[0].strip()
        value = parts[1]
        metadata[key] = value
    # get the date
    bdate = pd.to_datetime(metadata['Flight'].split(', ')[1])
    btime = pd.to_datetime(metadata['Flight'].split(', ')[2])
    bstart = btime.replace(year=bdate.year, month=bdate.month, day=bdate.day)

    # read data
    b1 = pd.read_csv('../data/balloon/FLT_010117_0000_PROC.txt.TXT', sep=';', index_col=False, skiprows=header_end + 1)

    # add the starting date to the timestamp field
    b1['Time Stamp'] = str(bdate.date()) + ' ' + b1['Time Stamp']
    b1['Time Stamp'] = pd.to_datetime(b1['Time Stamp'], format='%Y-%m-%d %H:%M:%S')

    # cumulative sum dates to correct the date changes
    time_lower = (b1['Time Stamp'].values[1:] - b1['Time Stamp'].values[0:-1]).astype(float) < 0
    elapsed_time = (b1['Elapsed Time'].values[1:] - b1['Elapsed Time'].values[0:-1]) >= 0
    days_ahead = np.cumsum(np.logical_and(time_lower, elapsed_time))
    days_ahead = np.insert(days_ahead, 0, 0)
    days_ahead = pd.to_timedelta(days_ahead, unit='D')
    b1['Time Stamp'] += days_ahead

    b1.set_index('Time Stamp', inplace=True)

    # xrb = xr.Dataset(b1, attrs=metadata)
    xrb = xr.Dataset(b1)
    xrb = xrb.expand_dims('Station').expand_dims('Profile')
    xrb.set_coords(
        ['Elapsed Time', 'Geopotential Height', 'Corrected Elevation', 'Latitude', 'Longitude', 'Geometric Height'],
        inplace=True)

    # set up the station coordinates
    xrb.coords['Station'] = ('Station', [metadata['Station Name (WMO #)']])
    xrb.coords['Station Height'] = ('Station', [metadata['Station Height']])
    xrb.coords['Station Latitude'] = ('Station', [metadata['Station Latitude']])
    xrb.coords['Station Longitude'] = ('Station', [metadata['Station Longitude']])

    # set up the profile coordinates
    xrb.coords['Profile'] = ('Profile', [bstart])
    xrb.coords['Flight'] = ('Profile', [metadata['Flight']])
    xrb.coords['File Name'] = ('Profile', [metadata['File Name']])
    xrb.coords['Observer Initial'] = ('Profile', [metadata['Observer Initial']])
    xrb.coords['Version #'] = ('Profile', [metadata['Version #']])
    return xrb