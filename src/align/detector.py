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
Detector lib for areadetector FLIR Oryx cameras.
"""

import time
import numpy as np

from align import pv
from align import log

DetectorIdle = 0
DetectorAcquire = 1


def init(global_PVs, params):
    if (params.detector_prefix == '2bmSP1:' or params.detector_prefix == '2bmSP2:'):   
        log.info(' ')                
        log.info('  *** init FLIR camera')
        log.info('  *** *** set detector to idle')
        global_PVs['Cam1Acquire'].put(DetectorIdle)
        pv.wait_pv(global_PVs['Cam1Acquire'], DetectorIdle, 2)
        log.info('  *** *** set detector to idle:  Done')
        time.sleep(1) 
        log.info('  *** *** set trigger mode to Off')
        global_PVs['Cam1TriggerMode'].put('Off', wait=True)    # 
        log.info('  *** *** set trigger mode to Off: done')
        time.sleep(1) 
        log.info('  *** *** set image mode to single')
        global_PVs['Cam1ImageMode'].put('Single', wait=True)   # here is where it crashes with (ValueError: invalid literal for int() with base 0: 'Single') Added 7 s delay before
        log.info('  *** *** set image mode to single: done')
        log.info('  *** *** set cam display to 1')
        global_PVs['Cam1Display'].put(1)
        log.info('  *** *** set cam display to 1: done')
        log.info('  *** *** set cam acquire')
        global_PVs['Cam1Acquire'].put(DetectorAcquire)
        pv.wait_pv(global_PVs['Cam1Acquire'], DetectorAcquire, 2) 
        log.info('  *** *** set cam acquire: done')
        log.info('  *** init FLIR camera: Done!')
    else:
        log.error('Detector %s is not supported' % params.detector_prefix)
        return


def set(global_PVs, params):

    if (params.detector_prefix == '2bmSP1:' or params.detector_prefix == '2bmSP2:'):
        log.info(' ')
        log.info('  *** setup FLIR camera')

        global_PVs['Cam1Acquire'].put(DetectorIdle)
        pv.wait_pv(global_PVs['Cam1Acquire'], DetectorIdle, 0.5)

        global_PVs['Cam1TriggerMode'].put('Off', wait=True)
        global_PVs['Cam1TriggerSource'].put('Line2', wait=True)
        global_PVs['Cam1TriggerOverlap'].put('ReadOut', wait=True)
        global_PVs['Cam1ExposureMode'].put('Timed', wait=True)
        global_PVs['Cam1TriggerSelector'].put('FrameStart', wait=True)
        global_PVs['Cam1TriggerActivation'].put('RisingEdge', wait=True)

        global_PVs['Cam1ImageMode'].put('Multiple')
        global_PVs['Cam1ArrayCallbacks'].put('Enable')
        global_PVs['Cam1FrameRateOnOff'].put(0)
        global_PVs['Cam1AcquireTimeAuto'].put('Off')

        global_PVs['Cam1AcquireTime'].put(float(params.exposure_time))

        wait_time_sec = int(params.exposure_time) + 0.5

        global_PVs['Cam1TriggerMode'].put('On', wait=True)
        log.info('  *** setup FLIR camera: Done!')
    
    else:
        log.error('Detector %s is not supported' % params.detector_prefix)
        return


def take_image(global_PVs, params):

    log.info('  ***  *** taking a single image')
   
    nRow = global_PVs['Cam1SizeY_RBV'].get()
    nCol = global_PVs['Cam1SizeX_RBV'].get()

    image_size = nRow * nCol

    global_PVs['Cam1NumImages'].put(1, wait=True)

    global_PVs['Cam1TriggerMode'].put('Off', wait=True)
    wait_time_sec = int(params.exposure_time) + 5

    global_PVs['Cam1Acquire'].put(DetectorAcquire, wait=True, timeout=1000.0)
    time.sleep(0.1)
    if pv.wait_pv(global_PVs['Cam1Acquire'], DetectorIdle, wait_time_sec) == False: # adjust wait time
        global_PVs['Cam1Acquire'].put(DetectorIdle)
    
    # Get the image loaded in memory
    img_vect = global_PVs['Image'].get(count=image_size)
    img = np.reshape(img_vect,[nRow, nCol])

    pixelFormat = global_PVs['Cam1PixelFormat_RBV'].get(as_string=True)
    if (pixelFormat == "Mono16"):
        pixel_f = 16
    elif (pixelFormat == "Mono8"):
        pixel_f = 8
    else:
        log.error('  ***  *** bit %s format not supported' % pixelFormat)
        exit()
    img_uint = np.mod(img.astype('int32'), 2**pixel_f).astype('uint16')    

    return img_uint


def take_dark_and_white(global_PVs, params):
    pv.close_shutters(global_PVs, params)
    log.info('  ***  *** acquire dark')
    dark_field = take_image(global_PVs, params)
    # plot(dark_field)

    pv.open_shutters(global_PVs, params)
    pv.move_sample_out(global_PVs, params)
    log.info('  ***  *** acquire white')
    white_field = take_image(global_PVs, params)
    # plot(white_field)

    pv.move_sample_in(global_PVs, params)

    return dark_field, white_field



