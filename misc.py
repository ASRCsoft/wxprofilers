import pandas as pd
import profileTimeSeries as pts
import lidar

def lidar_from_csv(rws, scans=None, location=None):
    # create a lidar object from Nathan's csv files
    # Timestamp,Configuration ID,Scan ID,LOS ID,Azimuth,Elevation,Range [m],RWS [m/s],DRWS [m/s],CNR [db],Confidence Index [%],Mean Error,Status
    csv = pd.read_csv(rws)

    # get the data
    data = csv.drop('LOS ID', 1).pivot(index='Timestamp', columns='Range [m]')
    data.index = pd.to_datetime(data.index)
    data_dict = pts.ProfileTimeSeries(data)

    # get the profiles
    profiles = csv[['Timestamp', 'LOS ID']].groupby(['Timestamp', 'LOS ID']).agg(lambda x: x.iloc[0])

    # get the scan info

    return lidar.Lidar(data_dict, profiles, scan=scan)
