import xml.etree.ElementTree
import numpy as np
import pandas as pd
import profileTimeSeries as pts
import profileInstrument as pins
import lidar
import math
import io
import re
import statsmodels.api as sm

def lidar_from_csv(rws, scans=None, location=None, scan_id=None):
    # create a lidar object from Nathan's csv files
    # Timestamp,Configuration ID,Scan ID,LOS ID,Azimuth,Elevation,Range [m],RWS [m/s],DRWS [m/s],CNR [db],Confidence Index [%],Mean Error,Status
    csv = pd.read_csv(rws)

    # get the data
    data = csv.drop('LOS ID', 1).pivot(index='Timestamp', columns='Range [m]')
    data.index = pd.to_datetime(data.index)
    data_dict = pts.ProfileTimeSeries(data)

    # get the profiles
    profiles = csv[['Timestamp', 'LOS ID']].groupby(['Timestamp', 'LOS ID']).agg(lambda x: x.iloc[0])
    # don't want a weird multi-index that includes LOS ID
    profiles.index = pd.DatetimeIndex(profiles['Timestamp'])

    # get the scan info
    if scans is not None:
        scan_xml = xml.etree.ElementTree.parse(scans).getroot()
        # in real life, we should search for the scan with the given id (if one is given) and get the info for that scan
        scan = scan_xml[0][1][2][0].attrib
    else:
        scan = None

    return lidar.Lidar(data_dict, profiles, scan=scan)

def mr_from_csv(file, scan='Zenith'):
    # read file
    f = open(file, "r")
    lines = f.readlines()
    f.close()

    # get the type of each line
    types = [ int(re.sub(",.*", "", re.sub("^[^,]*,[^,]*,", "", line))) for line in lines ]
    headers = np.where([ re.search("^Record", line) for line in lines ])

    # organize into csv's
    csvs = {}
    for n in np.nditer(headers):
        acceptable_types = np.array([1, 2, 3, 4])
        acceptable_types += types[n]
        is_type = [ types[m] in acceptable_types for m in range(len(types)) ]
        where_is_type = np.where(is_type)
        if where_is_type[0].size > 0:
            csv_lines = [ lines[m] for m in np.nditer(where_is_type) ]
            csv_lines.insert(0, lines[n])
            csv_string = ''.join(csv_lines)
            csv = io.StringIO(csv_string.decode('utf-8'))
            df = pd.read_csv(csv)
            csvs[str(types[n])] = df

    # rearrange measurements into multiindex dataframe:
    # mr_columns = csvs['400'].columns[4:-1].map(float)
    names = csvs['100']['Title']
    # iterables = [names, mr_columns]
    # mult_index = pd.MultiIndex.from_product(iterables, names=['Record Type', 'Range (km)'])
    # mr_index = pd.to_datetime(csvs['30']['Date/Time'][2:])
    # mr_data = pts.ProfileTimeSeries(index=mr_index, columns=mult_index, dtype='float')

    # just make it a hash for now. might go back to multiindex dataframe later
    mr_data = {}

    df400 = csvs['400']
    df400['Date/Time'] = pd.to_datetime(df400['Date/Time'])
    for n in range(csvs['100'].shape[0]):
        name = names[n]
        is_type = np.logical_and(df400['400'] == csvs['100']['Record Type'][n],
                                 df400['LV2 Processor'] == scan)
        df = df400.loc[is_type, df400.columns[4:-1]]
        df.index = df400.loc[is_type, 'Date/Time']
        df.columns = df.columns.map(float)
        #df.index = mr_index
        mr_data[name] = df

    #print(mr_data['Liquid (g/m^3)'].head())
    # good enough for now
    return(pins.ProfileInstrument(mr_data))






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
        resultsdf.loc[colnames[n],:] = df_data

    return resultsdf