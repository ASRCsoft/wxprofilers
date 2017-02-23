'''
each file gets read in from csv and converted to a dataFrame
each function takes a dataFrame (either temperature dataFrame
or a relative humidity dataFrame. Each function also returns
the appropriate dataFrame of what is needed EX: temp in celsius
'''


from pandas import *
import pandas as pd
#RAOB CSV

tempDF = pd.DataFrame.from_csv('/Users/arnoldas/Documents/Fall 2016/ASRC/microwave_radiometer_data/temperature.csv')
humidDF = pd.DataFrame.from_csv('/Users/arnoldas/Documents/Fall 2016/ASRC/microwave_radiometer_data/rel_humidity.csv')

#print tempDF

def pressureCalc(df):
    temp = df
    #.iloc first is the rows seperated by comma and then the column
    tempData = temp.iloc[:,3:-1]

    tempHeight = tempData.columns

    #conver heights from weird strings to floats
    tempHth = tempHeight.map(float)
    hpascals = 1013.25 * np.exp(-tempHth / 7)


    print "pressure"
    print hpascals

    return hpascals

def tempCalc(df):
    temp = df
    #.iloc first is the rows seperated by comma and then the column
    tempData = temp.iloc[:,3:-1]

    #calculation to convert temp from kelvin to celsius
    tempC = tempData - 273.15

    print "TempC"
    print tempC

    return tempC

def dewPointCalc(dfT, dfH):
    temp = dfT
    humid = dfH
    #.iloc first is the rows seperated by comma and then the column
    tempData = temp.iloc[:,3:-1]
    humidData = humid.iloc[:,3:-1]


    #calculations to get dew Points from relative humidity
    dewPoints = tempData - ((100 - humidData)/5)

    #dewpoints in kelvin if needed
    # print "DewPoints:"
    # print dewPoints
    # return dewPoints

    #comment out and uncomment dewPoints in levin if celcius not needed
    #calculation to convert dewpoint from kelvin to celcius
    dewC = dewPoints - 273.15

    print "DewPointsC"
    print dewC
    return dewC

def gpmCalc(df):
    temp = df
    #.iloc first is the rows seperated by comma and then the column
    tempData = temp.iloc[:,3:-1]

    tempHeight = tempData.columns

    #conver heights from weird strings to floats
    tempHth = tempHeight.map(float)

    print "tempHTH"
    print tempHth
    return tempHth




print "currently obtained data"
pressureCalc(tempDF)
tempCalc(tempDF)
dewPointCalc(tempDF,humidDF)
gpmCalc(tempDF)
