import profileTimeSeries as pts

class ProfileInstrument:
    def __init__(self, tsdict):
        self.data = tsdict
        self.profiles=profiles

    def export(self):
        # write a CF-compliant netCDF file containing the profileInstrument data
        pass

    # def __getattr__(self, item):
    #     print(item)
    #     print(self.data.values[0].__getattr__(item))
    #     # run the given function on each ProfileTimeSeries in self.data
    #     for key in self.data.keys():
    #         code = 'self.data["' + key + '"] = self.data["' + key + '"].' + item
    #         print(code)
    #         exec(code)
