import xml.etree.ElementTree
import pandas as pd
import profileTimeSeries as pts
import lidar

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
