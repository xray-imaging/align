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

from skimage.registration import phase_cross_correlation

from adjust import log
from adjust import detector
from adjust import pv
from adjust import config
from adjust import util
from epics import PV
import os

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

def adjust_roll(params):

    # angle_shift is the correction that is needed to apply to the rotation axis position
    # to align the Z stage on top of the rotary stage with the beam

    log.warning(' *** Adjusting roll ***')
   
    global_PVs = pv.init_general_PVs(params)

    global_PVs['SampleY'].put(params.pos0_y, wait=True)
    global_PVs['TomoScanStart'].put(1, wait=True, timeout=360000) # -1 - no timeout means timeout=0
    file_name0 = global_PVs['FPFileNameRBV'].get(as_string=True)

    global_PVs['SampleY'].put(params.pos1_y, wait=True)
    global_PVs['TomoScanStart'].put(1, wait=True, timeout=360000) # -1 - no timeout means timeout=0
    file_name1 = global_PVs['FPFileNameRBV'].get(as_string=True)

    log.info("wait 30 sec until data is transfered to the processing machine")
    time.sleep(30)
    cmd = f"tomopy recon --file-name={file_name0[6:]} --gridrec-padding True --rotation-axis-auto auto --reconstruction-type slice --config-update True"
    log.info(cmd)
    os.system(cmd)
    with open("/home/beams/TOMO/tomopy.conf") as fid:
        lines = fid.readlines()
        for line in lines:
            if 'rotation-axis = ' in line:
                axis0 = float(line[len('rotation-axis = '):])
    log.info('rotation center for the first file is %f' % axis0)                     
    cmd = f"tomopy recon --file-name={file_name1[6:]} --gridrec-padding True --rotation-axis-auto auto --reconstruction-type slice --config-update True"
    log.info(cmd)    
    os.system(cmd)
    with open("/home/beams/TOMO/tomopy.conf") as fid:
        lines = fid.readlines()
        for line in lines:
            if 'rotation-axis = ' in line:
                axis1 = float(line[len('rotation-axis = '):])
                
    log.info('rotation center for the second file is %f' % axis1) 
    pixel_size = global_PVs['ImagePixelSize'].get()      
    corr = float((axis1-axis0)*pixel_size/(params.pos1_y-params.pos0_y))
    angle = np.arctan(corr)/np.pi*180
    log.info('found roll error %f' % angle)                     
    log.info('correction in mm %f' % corr*68)        
    
    

