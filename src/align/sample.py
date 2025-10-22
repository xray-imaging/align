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
Module for sample alignment.
"""

import sys
import time
import numpy as np

from skimage.registration import phase_cross_correlation

from align import log
from align import detector
from align import pv
from align import config
from align import util
import matplotlib.pyplot as plt
    

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
            dark_field, white_field = detector.take_dark_and_white(global_PVs, params)
            if (what == 'resolution' ):
                find_resolution(params, dark_field, white_field)
                config.update_sphere(params)
            else:
                if(params.image_pixel_size==None):
                    # resolution must be measured at least once  
                    log.error('  *** Detector resolution is not determined. Please run adjust resolution first!')
                    time.sleep(2) # to avoid a calling callback function/epics.ca.ChannelAccessException 
                    exit()
                else:
                    dark_field, white_field = detector.take_dark_and_white(global_PVs, params)
                    if (what == 'center'):
                        adjust_rotation(params, dark_field, white_field)
                    
                    config.update_sphere(params)

    except  KeyError:
        log.error('  *** Some PV assignment failed!')
        pass


def find_resolution(params, dark_field, white_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Find resolution ***')
    log.info('  *** First image at X: %f mm' % (params.sample_in_x))
    log.info('  *** acquire first image')

    sample_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
    
    second_image_x_position = params.sample_in_x + params.off_axis_position
    log.info('  *** Second image at X: %f mm' % (second_image_x_position))
    global_PVs["SampleX"].put(second_image_x_position, wait=True, timeout=600.0)
    log.info('  *** acquire second image')
    sample_1 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
       
    log.info('  *** moving X stage back to %f mm position' % (params.sample_in_x))
    pv.move_sample_in(global_PVs, params)

    shift = phase_cross_correlation(sample_0, sample_1, normalization=None, upsample_factor=100)
    log.info('  *** shift X: %f, Y: %f' % (shift[0][1],shift[0][0]))
    image_pixel_size =  abs(params.off_axis_position) / np.linalg.norm(shift[0]) * 1000.0
    
    log.warning('  *** found resolution %f μm/pixel' % (image_pixel_size))    
    params.image_pixel_size = image_pixel_size          
    global_PVs['ImagePixelSize'].put(params.image_pixel_size, wait=True)


def adjust_rotation(params, dark_field, white_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Aligning rotation ***')              
    log.info('  *** sample 0')
    log.info('  ***  *** moving rotary stage to %f deg position ***' % float(0))
    global_PVs["Rotation"].put(float(0), wait=True, timeout=600.0)            
    log.error('  ***  *** acquire sample at %f deg position ***' % float(0))                                
    sample_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)    

    log.info('  *** sample 1')
    log.info('  ***  *** moving rotary stage to %f deg position ***' % float(180))                
    global_PVs["Rotation"].put(float(180), wait=True, timeout=600.0)
    log.error('  ***  *** acquire sample at %f deg position ***' % float(180))                                 
    sample_1 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
    
    shift0 = phase_cross_correlation(sample_0, sample_1[:,::-1], normalization=None, upsample_factor=100)[0][1]
    shift0/=2

    shift_top = phase_cross_correlation(sample_0[:100], sample_1[:100,::-1], normalization=None, upsample_factor=100)[0][1]
    shift_top/=2

    shift_bottom = phase_cross_correlation(sample_0[-100:], sample_1[-100:,::-1], normalization=None, upsample_factor=100)[0][1]
    shift_bottom/=2

    shift_center = phase_cross_correlation(sample_0[sample_0.shape[0]//2-50:sample_0.shape[0]//2+50], 
        sample_1[sample_0.shape[0]//2-50:sample_0.shape[0]//2+50,::-1], normalization=None, upsample_factor=100)[0][1]
    shift_center/=2

    log.info('  ')        
    log.info('  *** rotation axis shift %f pixels ***' % float(shift0))
    log.info('  *** rotation axis shift %f mm ***' % float(shift0*params.image_pixel_size/1000))

    log.info('  *** Additional values:  ***' )
    log.info('  *** rotation axis top    %f pixels ***' % float(shift_top))
    log.info('  *** rotation axis center %f pixels ***' % float(shift_center))
    log.info('  *** rotation axis bottom %f pixels ***' % float(shift_bottom))

    log.info('  *** Move rotation axis to middle?')
    if(params.ask):
        if util.yes_or_no('   *** Yes or No'):                
            global_PVs["SampleX"].put(global_PVs["SampleX"].get()+shift0*params.image_pixel_size/1000, wait=True, timeout=600.0)            
        else:
            log.warning(' No motion ')
            exit()


