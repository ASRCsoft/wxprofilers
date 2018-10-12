'''A python interface to the RRS Decoder.'''

import ctypes
rrs = ctypes.cdll.LoadLibrary('../src/rss.so')
rrs_decoder = rrs.rrs_decoder_
rrs_decoder.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                        ctypes.c_long, ctypes.c_long]
rrs_decoder.restype = None


def decode_rrs(path, outputs):
    '''Generate text files from radiosonde data in bufr format using the
RRS Decoder tool provided by NOAA.

    '''
    bufrin = bytes(path, 'utf-8')
    outpts = bytes(outputs, 'utf-8')
    rrs_decoder(bufrin, outpts, len(bufrin), len(outpts))
