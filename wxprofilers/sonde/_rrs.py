'''A python interface to the RRS Decoder.'''

from pathlib import Path
from wxprofilers import _rrs_decoder

def decode_rrs(bufrin, outputs, outdir=''):
    '''Run the RRS Decoder program provided by NOAA.

    bufrin (str): path to the radiosonde bufr file.
    outputs (str): desired output files (see RRS Decoder documentation).
    outdir (str): output directory.
    '''
    # try to make sure the path is handled correctly
    out = str(Path(outdir)) + '/'
    _rrs_decoder.rrs_decoder(bufrin, outputs, out)
