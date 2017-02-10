import pandas as pd
import lidar

def lidar_from_csv(rws, scans=None, location=None):
    # create a lidar object from Nathan's csv files
    # Timestamp,Configuration ID,Scan ID,LOS ID,Azimuth [°],Elevation [°],Range [m],RWS [m/s],DRWS [m/s],CNR [db],Confidence Index [%],Mean Error,Status
    csv = pd.read_csv(rws)
    data = csv.pivot(index='TimeStamp', columns='Range [m]')
    data.index = pd.to_datetime(data.index)
    data_dict = pts.ProfileTimeSeries(data)
    lidar.Lidar(data_dict)