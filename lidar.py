import numpy as np
import pandas as pd
import profileInstrument as pri

class Lidar(pri.ProfileInstrument):
    def __init__(self, tsdict,  profiles=None, location=None):
        self.data = tsdict
        self.profiles = profiles
        self.location = location
        self.wind = None

    def estimate_wind(self, method='Leosphere', seconds=15):
        if method=='Leosphere':
            if self.data['status'] is None or self.data['rws'] is None or
                self.profiles is None or 'LOS ID' not in self.profiles.columns:
                # raise an error
                pass
            x = pd.DataFrame(index=self.profiles.index, columns=self.data['rws'].columns)
            y = pd.DataFrame(index=self.profiles.index, columns=self.data['rws'].columns)
            z = pd.DataFrame(index=self.profiles.index, columns=self.data['rws'].columns)
            temp_prof = self.profiles[bool(self.data['status'][:,0]),'LOS ID']
            temp_rws = self.profiles[bool(self.data['rws'][:,0]),0]
            nprofiles = len(temp_prof)
            los0 = np.nan
            los2 = np.nan
            los0time = pd.NaT
            los2time = pd.NaT
            for n in range(0, nprofiles):
                isgood = False
                if temp_prof[n,'LOS ID']==0:
                    los0 = temp_rws[n,0]
                    los0time = temp_prof.index[n]
                    isgood = True
                if temp_prof[n,'LOS ID']==2:
                    los2 = temp_rws[n,0]
                    los2time = temp_prof.index[n]
                    isgood = True
                if isgood and abs((los2time - los0time).seconds) <= seconds:
                    x[temp_prof.index[n],0] = mean([los0, los2])



            #r = s.rolling(window=60)
        else:
            # no other methods are implemented
            pass
