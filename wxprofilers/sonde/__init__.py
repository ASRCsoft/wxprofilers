from ._rrs import decode_rrs
from ._sondepbl import heffter_pbl, bulk_richardson_pbl, liu_liang_pbl
import pandas as pd

# this makes the imported functions appear in sphinx docs
__all__ = ['decode_rrs', 'estimate_pbl']


# an interface to my sondepbl code
def estimate_pbl(method, height, pressure, temp,
                 rh=None, ws=None, u=None, v=None,
                 land=True, critical_threshold=.25):
    """Estimate PBL height using the methods described in :cite:`sivaraman_planetary_2013`.

    Args:
        method (str): Method to use to estimate PBL. One of 'richardson', 'heffter', or 'liu-liang'.
        height (ndarray): Array of heights in km.
        pressure (ndarray): Array of pressures in mb.
        temp (ndarray): Array of temperatures in °C.
        rh (ndarray): Array of relative humidities. Only required when method is 'richardson'.
        ws (ndarray): Array of wind speeds in m/s. Only required when method is 'liu-liang'.
        u (ndarray): Array of U wind components in m/s. Only required when method is 'richardson'.
        v (ndarray): Array of V wind components in m/s. Only required when method is 'richardson'.
        land (bool): Whether the sonde is over land, as opposed to ocean or ice. Only used when method is 'liu-liang'.
        critical_threshold (float): Bulk Richardson critical threshold. Only used when method is 'richardson'.


    Returns:
        float: Estimated PBL height in km.

    .. bibliography:: ../wxprofilers.bib

    """
    # organize a data frame similar to the LISTOS sonde data
    df = pd.DataFrame(data={'P': pressure, 'Height': height, 'Temp': temp})
    if method == 'heffter':
        return heffter_pbl(df)
    elif method == 'richardson':
        df['RH'] = rh
        df['U'] = u
        df['V'] = v
        return bulk_richardson_pbl(df, threshold=critical_threshold)
    elif method == 'liu-liang':
        df['WS'] = ws
        return liu_liang_pbl(df, land=land)
    else:
        raise Exception("Method should be one of 'richardson', 'heffter', or 'liuliang'.")
