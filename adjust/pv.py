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
Epics PV definitions
"""

import time

from epics import PV
from adjust import log

EPSILON = 0.1


def wait_pv(pv, wait_val, max_timeout_sec=-1):

    # wait on a pv to be a value until max_timeout (default forever)   
    # delay for pv to change
    time.sleep(.01)
    startTime = time.time()
    while(True):
        pv_val = pv.get()
        if type(pv_val) == float:
            if abs(pv_val - wait_val) < EPSILON:
                return True
        if (pv_val != wait_val):
            if max_timeout_sec > -1:
                curTime = time.time()
                diffTime = curTime - startTime
                if diffTime >= max_timeout_sec:
                    log.error('  *** ERROR: DROPPED IMAGES ***')
                    log.error('  *** wait_pv(%s, %d, %5.2f reached max timeout. Return False' % (pv.pvname, wait_val, max_timeout_sec))


                    return False
            time.sleep(.01)
        else:
            return True


def init_general_PVs(params):

    global_PVs = {}

    global_PVs['ShutterOpen'] = PV(params.shutter_open_pv_name  + '.VAL')
    global_PVs['ShutterClose'] = PV(params.shutter_close_pv_name + '.VAL')
    global_PVs['ShutterStatus'] = PV(params.shutter_status_pv_name + '.VAL')

    global_PVs['SampleX'] = PV(params.sample_x_pv_name + '.VAL')
    global_PVs['SampleXSet'] = PV(params.sample_x_pv_name + '.SET')
    global_PVs['SampleY'] = PV(params.sample_y_pv_name + '.VAL')
    global_PVs['SampleYSet'] = PV(params.sample_y_pv_name + '.SET')

    global_PVs['Rotation'] = PV(params.rotation_pv_name + '.VAL') 
    global_PVs['RotationRBV'] = PV(params.rotation_pv_name + '.RBV')
    global_PVs['RotationCnen'] = PV(params.rotation_pv_name + '.CNEN') 
    global_PVs['RotationAccl'] = PV(params.rotation_pv_name + '.ACCL') 
    global_PVs['RotationStop'] = PV(params.rotation_pv_name + '.STOP') 
    global_PVs['RotationSet'] = PV(params.rotation_pv_name + '.SET') 
    global_PVs['RotationVelo'] = PV(params.rotation_pv_name + '.VELO') 

    global_PVs['SampleXCent'] = PV(params.sample_x_center_pv_name + '.VAL')
    global_PVs['SampleZCent'] = PV(params.sample_z_center_pv_name + '.VAL') 
    global_PVs['SamplePitch'] = PV(params.sample_pitch_pv_name + '.VAL')
    global_PVs['SampleRoll'] = PV(params.sample_roll_pv_name + '.VAL')

    global_PVs['Focus'] = PV(params.focus_pv_name + '.VAL')

    global_PVs['ImagePixelSize'] = PV(params.image_pixel_size_pv_name + '.VAL')

    # detector pv's
    camera_prefix = params.detector_prefix + 'cam1:'

    global_PVs['CamManufacturer']      = PV(camera_prefix + 'Manufacturer_RBV')
    global_PVs['CamModel']             = PV(camera_prefix + 'Model_RBV')
    global_PVs['Cam1SerialNumber'] = PV(camera_prefix + 'SerialNumber_RBV')
    global_PVs['Cam1ImageMode'] = PV(camera_prefix + 'ImageMode')
    global_PVs['Cam1ArrayCallbacks'] = PV(camera_prefix + 'ArrayCallbacks')
    global_PVs['Cam1AcquirePeriod'] = PV(camera_prefix + 'AcquirePeriod')
    global_PVs['Cam1SoftwareTrigger'] = PV(camera_prefix + 'SoftwareTrigger') 
    global_PVs['Cam1AcquireTime'] = PV(camera_prefix + 'AcquireTime')
    global_PVs['Cam1FrameType'] = PV(camera_prefix + 'FrameType')
    global_PVs['Cam1AttributeFile'] = PV(camera_prefix + 'NDAttributesFile')
 
    global_PVs['Cam1SizeX'] = PV(camera_prefix + 'SizeX')
    global_PVs['Cam1SizeY'] = PV(camera_prefix + 'SizeY')
    global_PVs['Cam1NumImages'] = PV(camera_prefix + 'NumImages')
    global_PVs['Cam1TriggerMode'] = PV(camera_prefix + 'TriggerMode')
    global_PVs['Cam1Acquire'] = PV(camera_prefix + 'Acquire')

    global_PVs['Cam1SizeX_RBV'] = PV(camera_prefix + 'SizeX_RBV')
    global_PVs['Cam1SizeY_RBV'] = PV(camera_prefix + 'SizeY_RBV')

    global_PVs['Cam1MaxSizeX_RBV'] = PV(camera_prefix + 'MaxSizeX_RBV')
    global_PVs['Cam1MaxSizeY_RBV'] = PV(camera_prefix + 'MaxSizeY_RBV')
    global_PVs['Cam1PixelFormat_RBV'] = PV(camera_prefix + 'PixelFormat_RBV')


    image_prefix = params.detector_prefix + 'image1:'
    global_PVs['Image'] = PV(image_prefix + 'ArrayData')
    global_PVs['Cam1Display'] = PV(image_prefix + 'EnableCallbacks')

    manufacturer = global_PVs['CamManufacturer'].get(as_string=True)
    model = global_PVs['CamModel'].get(as_string=True)

    if model == 'Oryx ORX-10G-51S5M':
        log.info('Detector %s model %s:' % (manufacturer, model))
        global_PVs['Cam1AcquireTimeAuto'] = PV(params.detector_prefix + 'AcquireTimeAuto')
        global_PVs['Cam1FrameRateOnOff'] = PV(params.detector_prefix + 'FrameRateEnable')

        global_PVs['Cam1TriggerSource'] = PV(params.detector_prefix + 'TriggerSource')
        global_PVs['Cam1TriggerOverlap'] = PV(params.detector_prefix + 'TriggerOverlap')
        global_PVs['Cam1ExposureMode'] = PV(params.detector_prefix + 'ExposureMode')
        global_PVs['Cam1TriggerSelector'] = PV(params.detector_prefix + 'TriggerSelector')
        global_PVs['Cam1TriggerActivation'] = PV(params.detector_prefix + 'TriggerActivation')
    
    else:
        log.error('Detector %s model %s is not supported' % (manufacturer, model))
        return None        

    return global_PVs


def open_shutters(global_PVs, params):

    log.info(' ')
    log.info('  *** open_shutters')
    if params.testing:
        log.warning('  *** testing mode - shutters are deactivated !!!!')
    else:
        global_PVs['ShutterOpen'].put(str(params.shutter_open_value), wait=True)
        wait_pv(global_PVs['ShutterStatus'], params.shutter_status_open_value)
        log.info('  *** open_shutter: Done!') 


def close_shutters(global_PVs, params):

    log.info(' ')
    log.info('  *** close_shutters')
    if params.testing:
        log.warning('  *** testing mode - shutters are deactivated during the scans !!!!')
    else:
        global_PVs['ShutterClose'].put(params.shutter_close_value, wait=True)
        wait_pv(global_PVs['ShutterStatus'], params.shutter_status_close_value)
        log.info('  *** close_shutter: Done!')


def move_sample_out(global_PVs, params):

    axis = params.flat_field_axis

    log.info('move_sample_out axis: %s', axis)
    if axis in ('horizontal', 'both'):
        position = params.sample_out_x
        log.info('      *** *** Move Sample X in at: %f' % position)
        global_PVs['SampleX'].put(position, wait=True)

    if axis in ('vertical', 'both'):
        position = params.sample_out_y
        log.info('      *** *** Move Sample Y in at: %f' % position)
        global_PVs['SampleY'].put(position, wait=True)


def move_sample_in(global_PVs, params):

    axis = params.flat_field_axis

    log.info('move_sample_in axis: %s', axis)
    if axis in ('horizontal', 'both'):
        position = params.sample_in_x
        log.info('      *** *** Move Sample X in at: %f' % position)
        global_PVs['SampleX'].put(position, wait=True)

    if axis in ('vertical', 'both'):
        position = params.sample_in_y
        log.info('      *** *** Move Sample Y in at: %f' % position)
        global_PVs['SampleY'].put(position, wait=True)