# #########################################################################
# Copyright (c) 2020, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2019-2020. UChicago Argonne, LLC. This software was produced  #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Module for roll alignment with a stick
"""

import sys
import time
import numpy as np
import cupy as cp

from skimage.registration import phase_cross_correlation

from align import log
from align import detector
from align import pv
from align import config
from align import util
from epics import PV
import os
import h5py

def adjust(what, params):

    global_PVs = pv.init_general_PVs(params)

    try: 
        detector_sn = global_PVs['Cam1SerialNumber'].get()
        if ((detector_sn == None) or (detector_sn == 'Unknown')):
            log.error('*** The detector with EPICS IOC prefix %s is down' % params.detector_prefix)
            log.error('  *** Failed!')
        else:
            log.info('*** The detector with EPICS IOC prefix %s and serial number %s is on' \
                        % (params.detector_prefix, detector_sn))

            detector.init(global_PVs, params)
            detector.set(global_PVs, params) 
            if(what == 'roll'):
                adjust_roll(params)

    except  KeyError:
        log.error('  *** Some PV assignment failed!')
        pass

def _upsampled_dft(data, ups,
                    upsample_factor=1, axis_offsets=None):

    im2pi = 1j * 2 * np.pi
    tdata = data.copy()
    kernel = (cp.tile(cp.arange(ups), (data.shape[0], 1))-axis_offsets[:, 1:2])[
        :, :, None]*cp.fft.fftfreq(data.shape[2], upsample_factor)
    kernel = cp.exp(-im2pi * kernel)
    tdata = cp.einsum('ijk,ipk->ijp', kernel, tdata)
    kernel = (cp.tile(cp.arange(ups), (data.shape[0], 1))-axis_offsets[:, 0:1])[
        :, :, None]*cp.fft.fftfreq(data.shape[1], upsample_factor)
    kernel = cp.exp(-im2pi * kernel)
    rec = cp.einsum('ijk,ipk->ijp', kernel, tdata)

    return rec

def registration_shift(src_image, target_image, upsample_factor=1, space="real"):

    # assume complex data is already in Fourier space
    if space.lower() == 'fourier':
        src_freq = src_image
        target_freq = target_image
    # real data needs to be fft'd.
    elif space.lower() == 'real':
        src_freq = cp.fft.fft2(src_image)
        target_freq = cp.fft.fft2(target_image)

    # Whole-pixel shift - Compute cross-correlation by an IFFT
    shape = src_freq.shape
    image_product = src_freq * target_freq.conj()
    cross_correlation = cp.fft.ifft2(image_product)
    A = cp.abs(cross_correlation)
    maxima = A.reshape(A.shape[0], -1).argmax(1)
    maxima = cp.column_stack(cp.unravel_index(maxima, A[0, :, :].shape))

    midpoints = cp.array([cp.fix(axis_size / 2)
                            for axis_size in shape[1:]])

    shifts = cp.array(maxima, dtype=cp.float64)
    ids = cp.where(shifts[:, 0] > midpoints[0])
    shifts[ids[0], 0] -= shape[1]
    ids = cp.where(shifts[:, 1] > midpoints[1])
    shifts[ids[0], 1] -= shape[2]
    
    if upsample_factor > 1:
        # Initial shift estimate in upsampled grid
        shifts = cp.round(shifts * upsample_factor) / upsample_factor
        upsampled_region_size = cp.ceil(upsample_factor * 1.5)
        # Center of output array at dftshift + 1
        dftshift = cp.fix(upsampled_region_size / 2.0)

        normalization = (src_freq[0].size * upsample_factor ** 2)
        # Matrix multiply DFT around the current shift estimate

        sample_region_offset = dftshift - shifts*upsample_factor
        cross_correlation = _upsampled_dft(image_product.conj(),
                                                upsampled_region_size,
                                                upsample_factor,
                                                sample_region_offset).conj()
        cross_correlation /= normalization
        # Locate maximum and map back to original pixel grid
        A = cp.abs(cross_correlation)
        maxima = A.reshape(A.shape[0], -1).argmax(1)
        maxima = cp.column_stack(
            cp.unravel_index(maxima, A[0, :, :].shape))

        maxima = cp.array(maxima, dtype=cp.float64) - dftshift

        shifts = shifts + maxima / upsample_factor
            
    return shifts

def registration_shift_batch(u, w, upsample_factor=1, space="real"):
    res = np.zeros([u.shape[0], 2], dtype='float32')
    for k in range(0, u.shape[0]//60):
        ids = np.arange(k*60, (k+1)*60)
        # copy data part to gpu
        u_gpu = cp.array(u[ids])
        w_gpu = cp.array(w[ids])
        # Radon transform
        res_gpu = registration_shift(
            u_gpu, w_gpu, upsample_factor, space)
        # copy result to cpu
        res[ids] = res_gpu.get()
    return res

def adjust_roll(params):

    # angle_shift is the correction that is needed to apply to the rotation axis position
    # to align the Z stage on top of the rotary stage with the beam

   
    log.warning(' *** Adjusting roll ***')
   
    global_PVs = pv.init_general_PVs(params)
    for k in np.arange(-0.06,0.061,0.01):
        print(k)
        global_PVs['SampleRoll'].put(k,wait=True)
        global_PVs['SampleY'].put(params.pos0_y, wait=True)
        global_PVs['TomoScanStart'].put(1, wait=True, timeout=360000) # -1 - no timeout means timeout=0
        file_name0 = global_PVs['FPFullFileNameRBV'].get(as_string=True)[6:]
        # file_name0 = '/data/2021-11/Nikitin/test_006.h5'
        global_PVs['SampleY'].put(params.pos1_y, wait=True)
        global_PVs['TomoScanStart'].put(1, wait=True, timeout=360000) # -1 - no timeout means timeout=0
        file_name1 = global_PVs['FPFullFileNameRBV'].get(as_string=True)[6:]
        # file_name1 = '/data/2021-11/Nikitin/test_007.h5'

        log.info("wait 20 sec until data is transfered to the processing machine")
        time.sleep(20)

        with h5py.File(file_name0) as fid:  
            flat = np.mean(fid['/exchange/data_white'][:],axis=0)
            dark = np.mean(fid['/exchange/data_dark'][:],axis=0)
            data = fid['/exchange/data'][:]
        data = (data-dark)/(flat-dark+1e-3)

        halfnangles = data.shape[0]//2
        data[halfnangles:] = data[halfnangles:,:,::-1]
        shifts0 = registration_shift_batch(data[:halfnangles], data[halfnangles:], upsample_factor=10, space="real")
        # print(shifts0)
        
        with h5py.File(file_name1) as fid:  
            flat = np.mean(fid['/exchange/data_white'][:],axis=0)
            dark = np.mean(fid['/exchange/data_dark'][:],axis=0)
            data = fid['/exchange/data'][:]
        data = (data-dark)/(flat-dark+1e-3)

        halfnangles = data.shape[0]//2
        data[halfnangles:] = data[halfnangles:,:,::-1]
        # shifts = np.zeros([halfnangles],dtype='float32')
        shifts1 = registration_shift_batch(data[:halfnangles], data[halfnangles:], upsample_factor=10, space="real")
        # print(shifts1)
        print(f'average shift0 for {k=}',np.median(shifts0[0][1]))
        print(f'average shift1 for {k=}',np.median(shifts1[0][1]))
    # # log.info("wait 10 sec until data is transfered to the processing machine")
    # # time.sleep(10)
    # cmd = f"tomopy recon --file-name={file_name0[6:]} --gridrec-padding True --rotation-axis-auto auto --reconstruction-type slice --config-update True --fix-nan-and-inf True"
    # log.info(cmd)
    # os.system(cmd)
    # with open(params.tomopy_config) as fid:
    #     lines = fid.readlines()
    #     for line in lines:
    #         if 'rotation-axis = ' in line:
    #             axis0 = float(line[len('rotation-axis = '):])
    # log.info('rotation center for the first file is %f' % axis0)                     
    # cmd = f"tomopy recon --file-name={file_name1[6:]} --gridrec-padding True --rotation-axis-auto auto --reconstruction-type slice --config-update True --fix-nan-and-inf True"
    # log.info(cmd)    
    # os.system(cmd)
    # with open(params.tomopy_config) as fid:
    #     lines = fid.readlines()
    #     for line in lines:
    #         if 'rotation-axis = ' in line:
    #             axis1 = float(line[len('rotation-axis = '):])
                
    # log.info('rotation center for the second file is %f' % axis1) 
    # pixel_size = global_PVs['ImagePixelSize'].get()     
    # axis0 = np.median(shifts0[0][1]) 
    # axis1 = np.median(shifts1[0][1]) 
    # corr = np.tan(np.arcsin(float((axis1-axis0)*pixel_size*1e-3/(params.pos1_y-params.pos0_y)))*68)
    # angle = np.arcsin(float((axis1-axis0)*pixel_size*1e-3/(params.pos1_y-params.pos0_y)))/np.pi*180
    # log.info('found roll error %f' % angle)                     
    # log.info('correction in mm %f' % corr)        
    
    

