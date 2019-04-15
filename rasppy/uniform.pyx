'''Fast 2D uniform filter.'''

import numpy as np

cdef update_top(double[:] x, double bound, Py_ssize_t cur):
    '''Update the top (or right) bound of the window.'''
    cdef int xlength = x.shape[0]
    while cur + 1 < xlength and x[cur + 1] < bound:
        cur += 1
    return cur

cdef update_bottom(double[:] x, double bound, Py_ssize_t cur):
    '''Update the bottom (or left) bound of the window.'''
    cdef int xlength = x.shape[0]
    while x[cur] <= bound:
        cur += 1
    return cur

def uniform_filter(double[:, :] arr, double[:] x, double[:] y, double dx, double dy):
    '''Apply a uniform filter with window size (dx, dy).'''
    cdef int xlength = arr.shape[0]
    cdef int ylength = arr.shape[1]
    cdef Py_ssize_t leftx = 0
    cdef Py_ssize_t rightx = 0
    cdef Py_ssize_t topy = 0
    cdef Py_ssize_t bottomy = 0
    cdef Py_ssize_t new_index
    cdef Py_ssize_t ix = 0
    cdef Py_ssize_t iy = 0
    cdef Py_ssize_t ix2 = 0
    cdef Py_ssize_t iy2 = 0
    cdef double sum = 0
    cdef int count = 0
    cdef double bound
    cdef double[:, :] out = np.empty((xlength, ylength))
    cdef double[:] ysum = np.zeros(ylength)
    cdef int[:] ycount = np.zeros(ylength).astype(np.int32)
    # get the means
    for ix in range(xlength):
        # update the row sums
        # update the upper bound
        bound = x[ix] + dx
        new_index = update_top(x, bound, rightx)
        for iy in range(ylength):
            for ix2 in range(rightx, new_index):
                ysum[iy] += arr[ix2, iy]
                ycount[iy] += 1
        rightx = new_index
        # update the lower bound
        bound = x[ix] - dx
        new_index = update_bottom(x, bound, leftx)
        for iy in range(ylength):
            for ix2 in range(leftx, new_index):
                ysum[iy] -= arr[ix2, iy]
                ycount[iy] -= 1
        leftx = new_index
        # reset sum, count, and y window bounds to zero
        sum = 0
        count = 0
        bottomy = 0
        topy = 0
        for iy in range(ylength):
            # update the window sums
            # update the upper bound
            bound = y[iy] + dy
            new_index = update_top(y, bound, topy)
            for iy2 in range(topy, new_index):
                sum += ysum[iy2]
                count += ycount[iy2]
            topy = new_index
            # update the lower bound
            bound = y[iy] - dy
            new_index = update_bottom(y, bound, bottomy)
            for iy2 in range(bottomy, new_index):
                sum -= ysum[iy2]
                count -= ycount[iy2]
            bottomy = new_index
            # update the output array
            out[ix, iy] = sum / count
    return out
