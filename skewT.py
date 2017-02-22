'''
Required packages to run SHARPpy:
PySide (for plotting)
Numpy (for running SHARPTAB routines)
'''
import numpy
import pandas as pd

from pandas import *
import csv
#from ggplot import *
from csv import reader
import itertools
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np; np.random.seed(0)
import seaborn as sns; sns.set()
# import sharppy
# import sharppy.sharptab.profile as profile
# import sharppy.sharptab.interp as interp
# import sharppy.sharptab.winds as winds
# import sharppy.sharptab.utils as utils
# import sharppy.sharptab.params as params
# import sharppy.sharptab.thermo as thermo


from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from metpy.calc import resample_nn_1d
from metpy.io import get_upper_air_data
from metpy.io.upperair import UseSampleData
from metpy.plots import SkewT

from metpy.units import units


import numpy as np
my_array = np.array([0,1,2,3])

#changing it from an int array to a string array
str_array = my_array.astype(str)

for i in my_array:
    print i*4

for i in str_array:
    print i*4

#np.genfromtxt('file.csv', delimiter=',')

a = np.array([[1,2,3],[4,5,6]])

#print a

#you can index the array where a>=3
b = a[ a>=3 ]

#print b
'''
plt.plot(tmsrs.T)
plt.show
'''
#to get the 5th column
#timepoint5 = tmsrs.T[5]

#Metpy
temp = read_csv('/Users/arnoldas/Documents/Fall 2016/ASRC/microwave_radiometer_data/temperature.csv')
humid = read_csv('/Users/arnoldas/Documents/Fall 2016/ASRC/microwave_radiometer_data/rel_humidity.csv')

#.iloc first is the rows seperated by comma and then the column
tempData = temp.iloc[:,3:-1]
humidData = humid.iloc[:,3:-1]

print "TEMPDATA"
print tempData

#calculation to convert temp from kelvin to celcius
tempC = tempData - 273.15

print "TempC"
print tempC

print "REL_HUMID"
print humidData

tempHeight = tempData.columns
humidHeight = humidData.columns

#conversion from km to pressure
print "TEMPCOLS"
print tempHeight

#conver heights from weird strings to floats
tempHth = tempHeight.map(float)
humidHth = humidHeight.map(float)

print "tempHTH"
print tempHth

#get the heights out of the header
#hpascals = 1013.25 * exp(-ranges / 7)
hpascals = 1013.25 * np.exp(-tempHth / 7)

print "pressure"
print hpascals

#calculations to get dew Points from relative humidity
dewPoints = tempData - ((100 - humidData)/5)

print "DewPoints:"
print dewPoints

#calculation to convert dewpoint from kelvin to celcius
dewC = dewPoints - 273.15

print "DewPointsC"
print dewC

# plt.plot(tempData.iloc[10,:], tempHth, 'r-')
# #plt.plot(tempData)
# #plt.plot(tempHth)
# #plt.plot(prof.dwpc, prof.hght, 'g-')
# plt.xlabel("Temperature [K]")
# plt.ylabel("Height [kilometers]")
# #plt.grid()
# plt.show()


# Change default to be better for skew-T
plt.rcParams['figure.figsize'] = (9, 9)
skew = SkewT()
skew.plot(hpascals, tempC.iloc[0,:] ,'r')
skew.plot( hpascals, dewC.iloc[0,:], 'g')
# # Add the relevant special lines
#blue lines are the wet adiabats
#red lines are the dry adiabats
#green short lines are teh mixing lines
skew.plot_dry_adiabats()
skew.plot_moist_adiabats()
skew.plot_mixing_lines()
skew.ax.set_ylim(1100, 200)
plt.show()


'''
rel_humid = read_csv('/Users/arnoldas/Documents/Fall 2016/ASRC/microwave_radiometer_data/rel_humidity.csv')

testtemp = np.genfromtxt('/Users/arnoldas/Documents/Fall 2016/ASRC/microwave_radiometer_data/temperature.csv', delimiter=',' ,skip_header=1, skip_footer=1)

#print testtemp


temp['Date/Time'] = to_datetime(temp['Date/Time'])

for row in temp:
    range = row
    #print range


#print temp['Date/Time']

#print temp

longtmps = np.array(temp)

newtmps = longtmps[ longtmps>100 ]

#print longtmps
#print newtmps

tmp = temp.drop('Date/Time', axis =1)
tmp.index = temp['Date/Time']

#print "testing", tmp.index
#ys = tmp.columns.map(int)

times = tmp.index.map(mdates.date2num)

#print times

#tempTest = [236, 233, 277]


#nums = xrange(0, times.shape[1:1])
#plt.plot(times)
#plt.plot(times.T)
#plt.show()
#creating profile objects:
#prof = profile.create_profile(profile='default', tmpc=tempTest, missing=-9999, strictQC=True)

# import matplotlib.pyplot as plt
# plt.plot(times)
# plt.plot(tempTest)
# #plt.plot(prof.tmpc, prof.hght, 'r-')
# #plt.plot(prof.dwpc, prof.hght, 'g-')
# #plt.barbs(40*np.ones(len(prof.hght)), prof.hght, prof.u, prof.v)
# plt.xlabel("Temperature [C]")
# plt.ylabel("Height [m above MSL]")
# plt.grid()
# plt.show()
'''
