'''
This file uses the dataframe with time index
Main use is for plotting heatmaps using matplotlib
Includes the core functions handling the data
for plotting and agrigating by time
'''
import pandas as pd

class ProfileTimeSeries(pd.DataFrame):