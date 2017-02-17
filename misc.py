import xml.etree.ElementTree
import numpy as np
import pandas as pd
import profileTimeSeries as pts
import lidar
import math
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
        if any(se == 0):
            print("statsmodels says standard error is zero-- that's not right!")
            print(len(los[notnan].unique()))
            exit()
        coefs[np.logical_or(se > max_se, np.logical_not(np.isfinite(se)))] = np.nan
        df_data = np.concatenate((coefs, results.bse))
        resultsdf.loc[colnames[n],:] = df_data

    return resultsdf