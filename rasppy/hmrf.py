'''
Estimate measurement confidence using a hidden markov random field model
'''

from rasppy.segmentation import Segmentation
from rasppy.segmentation.segmentation import nonzero, log
import numpy as np
import xarray as xr
from scipy.ndimage import uniform_filter, median_filter, gaussian_filter

# nonzero = lambda x: np.maximum(x, 1e-50)
# log = lambda x: np.log(nonzero(x))

class Hmrf(Segmentation):

    def __init__(self, data, local_values=0, rws_range=(-32, 32),
                 mask=None, mu=None, sigma=None,
                 ppm=None, prior=None, U=None,
                 ngb_size=None, beta=None):
        # Segmentation init
        super(Hmrf, self).__init__(data, mask, mu, sigma, ppm, prior, U,
                                   ngb_size, beta)
        
        # new stuff
        self.rws_min = rws_range[0]
        self.rws_max = rws_range[1]
        local_values = local_values.squeeze()
        self.estimates = local_values[mask]

    def vm_step(self, freeze=()):
        classes = list(range(self.nclasses))
        for i in freeze:
            classes.remove(i)

        for i in classes:
            if i == 0:
                # the wind class
                P = self.ppm[..., i][self.mask].ravel()
                Z = nonzero(P.sum())
                tmp = (self.data - self.estimates).T * P.T
                mu = tmp.sum(1) / Z
                mu_ = mu.reshape((len(mu), 1))
                sigma = np.dot(tmp, self.data - self.estimates) / Z - np.dot(mu_, mu_.T)
                self.mu[i] = mu
                self.sigma[i] = sigma
            else:
                # the noise class -- only estimating CNR params
                P = self.ppm[..., i][self.mask].ravel()
                Z = nonzero(P.sum())
                tmp = self.data[:, 1].T * P.T
                # mu = tmp.sum(1) / Z
                # mu_ = mu.reshape((len(mu), 1))
                # weighted mean
                mu = tmp.sum() / Z
                # weighted variance
                sigma = np.sum(P * (self.data[:, 1] - self.mu[i, 1])**2) / Z
                self.mu[i, 1] = mu
                self.sigma[i, 1, 1] = sigma

    def log_external_field(self):
        """
        Compute the logarithm of the external field, where the
        external field is defined as the likelihood times the
        first-order component of the prior.
        """

        # these are the likelihoods without considering the neighbor
        # relationships!
        lef = np.zeros([self.data.shape[0], self.nclasses])

        for i in range(self.nclasses):
            if i == 0:
                # this is the wind data
                # centered_data = self.data - self.mu[i]
                centered_data = self.data - self.estimates - self.mu[i]
                if self.nchannels == 1:
                    inv_sigma = 1. / nonzero(self.sigma[i])
                    norm_factor = np.sqrt(2 * np.pi * inv_sigma.squeeze())
                else:
                    inv_sigma = np.linalg.inv(self.sigma[i])
                    # this is for the 1/(sqrt(2pi*sigma)) term!
                    norm_factor = 1. / np.sqrt(2 * np.pi * \
                        nonzero(np.linalg.det(self.sigma[i])))
                # this is the log(exp(-.5(x-mu)^2/sigma^2)) !
                maha_dist = np.sum(centered_data * np.dot(inv_sigma,
                                                          centered_data.T).T, 1)
                lef[:, i] = -.5 * maha_dist
                lef[:, i] += log(norm_factor)
            else:
                # this is the noise data
                centered_data = self.data[:, 1] - self.mu[i, 1]
                # if self.nchannels == 1:
                # this parts calculates the likelihood of just the CNR (normally distributed)
                inv_sigma = 1. / nonzero(self.sigma[i, 1, 1])
                norm_factor = np.sqrt(2 * np.pi * inv_sigma)
                maha_dist = centered_data**2 * inv_sigma
                lef[:, i] = -.5 * maha_dist
                lef[:, i] += log(norm_factor)
                # likelihood of just the RWS (uniformly distributed)
                lef[:, i] += log(1 / (self.rws_max - self.rws_min))

        if self.prior is not None:
            lef += log(self.prior)

        return lef


class LidarSamples(Segmentation):
    '''
    A class for estimating HMRF parameters from samples of lidar data
    '''

    def __init__(self, samples, nclasses=2):
        '''
        Samples should be a list of segmentation objects
        '''
        self.samples = samples
        self.data = np.concatenate([ s.data for s in self.samples ])
        self.estimates = np.concatenate([ s.estimates for s in self.samples ])
        self.nclasses = nclasses
        self.is_ppm = False
        self.mu = np.array([[0, 0], [0, -31.5]])
        self.sigma = np.array([[[.5, 0], [0, 2]], [[300, 0], [0, 3]]])

    def ve_step(self):
        for s in self.samples:
            s.ve_step()
    
    def vm_step(self, freeze=()):
        '''
        Estimate parameters from samples
        '''
        classes = list(range(self.nclasses))
        for i in freeze:
            classes.remove(i)

        for i in classes:
            # P = self.ppm[..., i][self.mask].ravel()
            P = np.concatenate([ s.ppm[..., i][s.mask].ravel() for s in self.samples ])
            
            if i == 0:
                # the wind class                
                Z = nonzero(P.sum())
                tmp = (self.data - self.estimates).T * P.T
                # tmp = np.concatenate([ s.data - s.estimates for s in self.samples ]).T * P.T
                mu = tmp.sum(1) / Z
                mu_ = mu.reshape((len(mu), 1))
                sigma = np.dot(tmp, self.data - self.estimates) / Z - np.dot(mu_, mu_.T)
                # set the new parameter values for the samples
                for s in self.samples:
                    s.mu[i] = mu
                    s.sigma[i] = sigma
                # also set the parameter values for this object!
                self.mu[i] = mu
                self.sigma[i] = sigma
            else:
                # the noise class -- only estimating CNR params
                Z = nonzero(P.sum())
                tmp = self.data[:, 1].T * P.T
                # mu = tmp.sum(1) / Z
                # mu_ = mu.reshape((len(mu), 1))
                # weighted mean
                mu = tmp.sum() / Z
                # weighted variance
                sigma = np.sum(P * (self.data[:, 1] - self.mu[i, 1])**2) / Z
                # set the new parameter values for the samples
                for s in self.samples:
                    s.mu[i, 1] = mu
                    s.sigma[i, 1, 1] = sigma
                # also set the parameter values for this object!
                self.mu[i, 1] = mu
                self.sigma[i, 1, 1] = sigma

                
def make_segmentation(rws, cnr, median_size=(7, 59),
                      gaussian_sigma=(1, 2), **seg_args):
    '''
    Make a nipy-style segmentation object given radial wind speed and
    CNR arrays

    seg_args are passed to rasppy.segmentation.Segmentation

    '''
    # get the filtered values
    frws = xr.DataArray(data=np.empty(rws.shape), dims=rws.dims, coords=rws.coords)
    fcnr = xr.DataArray(data=np.empty(rws.shape), dims=rws.dims, coords=rws.coords)
    scan_not_nan = ~np.isnan(cnr).any('Range')
    frws[:,scan_not_nan] = median_filter(rws.sel(Time=scan_not_nan), size=median_size)
    frws[:,~scan_not_nan] = np.NaN
    fcnr[:,scan_not_nan] = gaussian_filter(cnr.sel(Time=scan_not_nan), sigma=gaussian_sigma)
    fcnr[:,~scan_not_nan] = np.NaN
    
    # put together the input values
    da = xr.concat([rws, cnr], 'series').transpose('Time', 'Range', 'series')
    local_values = xr.concat([frws, fcnr], 'series').transpose('Time', 'Range', 'series')
    scan_is_complete = ~np.isnan(da).any(['Range', 'series'])
    da = da.isel(Time=scan_is_complete)
    local_values = local_values.isel(Time=scan_is_complete)

    return Segmentation(da.values, local_values=local_values.values, **seg_args)
