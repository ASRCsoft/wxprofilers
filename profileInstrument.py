class ProfileInstrument:

    def __init__(self, file = None):
        # takes a netCDF file, organizes data
        self.data = {}

    def export(self):
        # writes a CF-compliant netCDF file containing the profileInstrument data
