# -*- coding: UTF-8 -*-
import xml.etree.ElementTree
import numpy as np
import pandas as pd
import xarray as xr
import profileTimeSeries as pts
import math
import io
import re
import statsmodels.api as sm


def lidar_from_csv(rws, scans=None, location=None, scan_id=None, lidar=None, loc=None):
    # create a lidar object from Nathan's csv files
    # Timestamp,Configuration ID,Scan ID,LOS ID,Azimuth,Elevation,Range [m],RWS [m/s],DRWS [m/s],CNR [db],Confidence Index [%],Mean Error,Status
    csv = pd.read_csv(rws)
    profile_vars = ['LOS ID', 'Configuration ID', 'Azimuth [°]', 'Elevation [°]']
    #profile_vars2 = ['scan', 'LOS ID', 'Timestamp', 'Configuration ID', 'Azimuth [°]', 'Elevation [°]']
    #profile_vars = ['Configuration ID', 'Azimuth [°]', 'Elevation [°]']



    # get the data
    data = csv.drop(profile_vars, 1).pivot(index='Timestamp', columns='Range [m]')
    data.index = pd.to_datetime(data.index)

    # get the profiles
    profiles = csv[['Timestamp', 'LOS ID']].drop_duplicates()
    # don't want a weird multi-index that includes LOS ID
    profiles.index = pd.DatetimeIndex(profiles['Timestamp'])

    # new!
    profile_vars.append('Timestamp')
    measurement_vars = ['RWS [m/s]', 'DRWS [m/s]', 'CNR [db]', 'Confidence Index [%]', 'Mean Error', 'Status']
    csv_profs = csv[profile_vars].groupby('Timestamp').agg(lambda x: x.iloc[0])
    #csv_profs.reset_index(inplace=True)
    #csv_profs['Timestamp'] = pd.to_datetime(csv_profs['Timestamp'])
    #return csv_profs

    h1 = {}
    coords = {'Timestamp': ('Timestamp', data.index), 'Range [m]': data.columns.levels[1]}
    if lidar is not None:
        coords['lidar'] = [lidar]
        if loc is not None:
            coords['latitude'] = ('lidar', [loc[0]])
            coords['longitude'] = ('lidar', [loc[1]])
    profile_vars.remove('Timestamp')  # get rid of 'Timestamp'
    #csv_profs2 = csv_profs.pivot(index='scan', columns='LOS ID')
    #coords = {'scan': csv_profs['scan'].unique(), 'LOS ID': range(nlos), 'Range [m]': data.columns.levels[1]}
    #profile_vars.remove('LOS ID')
    #profile_vars.remove('scan')
    #return csv_profs['scan']
    #data['scan'] = csv_profs['scan'].values
    #data['LOS ID'] = csv_profs['LOS ID'].values
    #data.set_index(['scan', 'LOS ID'], inplace=True)

    # get the scan info
    if scans is not None:
        scan_xml = xml.etree.ElementTree.parse(scans).getroot()
        # in real life, we should search for the scan with the given id (if one is given) and get the info for that scan
        scan = scan_xml[0][1][2][0].attrib
        nlos = None
        if scan['mode'] == 'dbs':
            nlos = 5
        if nlos is not None:
            # if we can get nlos, add a multiindex 'profile' coordinate that includes scan # and LOS ID as dimensions
            #profile_vars.remove('LOS ID')  # which means LOS ID is no longer one of these

            # set up the scan numbers
            # get the cumulative sum of the zero's-- clever, I like!
            csv_profs['scan'] = np.cumsum(csv_profs['LOS ID'] == 0)
            profile_vars.append('scan') # now the scan is a profile variable

            # set up the profile multiindex -- nope don't do this
            # profile = pd.MultiIndex.from_arrays([csv_profs['scan'], csv_profs['LOS ID']], names=('scan', 'LOS ID'))
            # coords['profile'] = ('profile', profile)
    else:
        scan = None


    for scan_type in profile_vars:
        coords[scan_type] = ('Timestamp', csv_profs[scan_type])
        #coords[scan_type] = (('scan', 'LOS ID'), csv_profs2[scan_type])
    for level in measurement_vars:
        h1[level] = (('Timestamp', 'Range [m]'), xr.DataArray(data[level]))
        #h1[level] = (('Range [m]', 'scan', 'LOS ID'), xr.DataArray(data[level]).unstack('dim_0'))
        #h1[level] = (('dim_0', 'Range [m]'), xr.DataArray(data[level]))
    #return h1
    #return coords
    xarray = xr.Dataset(h1, coords=coords, attrs={'scan': scan})
    xarray.rename({'RWS [m/s]': 'RWS', 'DRWS [m/s]': 'DRWS', 'CNR [db]': 'CNR',
                   'Confidence Index [%]': 'Confidence Index', 'Range [m]': 'Range',
                   'Azimuth [°]': 'Azimuth', 'Elevation [°]': 'Elevation'}, inplace=True)
    xarray['RWS'].attrs['units'] = 'm/s'
    xarray['DRWS'].attrs['units'] = 'm/s'
    xarray['CNR'].attrs['units'] = 'db'
    xarray['Confidence Index'].attrs['units'] = 'percent'
    xarray.coords['Range'].attrs['units'] = 'm'
    xarray.coords['Azimuth'].attrs['units'] = 'degrees'
    xarray.coords['Elevation'].attrs['units'] = 'degrees'
    return xarray


def mr_from_csv(file, scan='Zenith'):
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
    mrds.coords['dim_1'] = map(float, mrxr.coords['dim_1'].values)
    mrds.rename({'400': 'Record Type', 'dim_1': 'Range'}, inplace=True)
    mrds.coords['Record Type'] = names
    mrds.coords['Range'].attrs['units'] = 'km'
    mrds['Measurement'].attrs['units'] = record_unit_dict
    mrds.set_coords('Date/Time', inplace=True)
    return mrds


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