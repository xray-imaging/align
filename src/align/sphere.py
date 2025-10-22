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
Module for sphere alignment.
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
    
SPHERE_DIAMETER = 0.5     # in mm
GAP = 0.02                # empty space between the shere and the edge of the FOV used when measuring roll, in mm 

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
            plt.imshow(white_field)
            # plt.show()
            if (what == 'resolution' ):
                find_resolution(params, dark_field, white_field, angle_shift = -0.7)
                config.update_sphere(params)
            else:
                if(params.image_pixel_size==None):
                    # resolution must be measured at least once  
                    log.error('  *** Detector resolution is not determined. Please run adjust resolution first!')
                    time.sleep(2) # to avoid a calling callback function/epics.ca.ChannelAccessException 
                    exit()
                else:
                    dark_field, white_field = detector.take_dark_and_white(global_PVs, params)
                    if (what == 'focus'):
                        adjust_focus(params)
                    if (what == 'center'):
                        adjust_center(params, dark_field, white_field)
                        #adjust_center2(params, dark_field, white_field)
                    if(what == 'roll'):
                        adjust_roll(params, dark_field, white_field, angle_shift = -0.7)
                    if(what == 'pitch'):           
                        adjust_pitch(params, dark_field, white_field, angle_shift = -0.7)
                    if(what == 'roll') or (what == 'pitch'):
                        # align center again for higher accuracy    
                        adjust_center(params, dark_field, white_field)
                    if(what == 'rotary'):
                        adjust_rotary(params, dark_field, white_field)
                    if(what == 'theta'):
                        adjust_theta(params, dark_field, white_field)

                    config.update_sphere(params)

    except  KeyError:
        log.error('  *** Some PV assignment failed!')
        pass

def adjust_theta(params, dark_field, white_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Adjusting Sample X ***')              
    angles = np.arange(params.theta_start, params.theta_end, params.theta_step)
    distances_x =[]
    for ang in angles:
        print(ang, params.pos0_x, params.pos1_x)
        global_PVs["SampleTheta"].put(ang, wait=True, timeout=600.0) 
        global_PVs["SampleX"].put(params.pos0_x, wait=True, timeout=600.0) 
        sphere = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field) 
        cmass = util.center_of_mass(sphere)
        cmass_pos0_x = float(cmass[1])
        global_PVs["SampleX"].put(params.pos1_x, wait=True, timeout=600.0) 
        sphere = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field) 
        cmass = util.center_of_mass(sphere)
        cmass_pos1_x = float(cmass[1])
        distance = (cmass_pos0_x - cmass_pos1_x) * params.image_pixel_size
        distances_x.append(distance)


    # Ensure numpy arrays
    angles = np.array(angles)
    distances_x = np.array(distances_x)

    # Fit a parabola (degree 2)
    coeffs = np.polyfit(angles, distances_x, 2)
    poly = np.poly1d(coeffs)
    print("Fit coefficients:", coeffs)

    # Vertex of the parabola (min or max depending on sign of a)
    a, b, c = coeffs
    angle_min = -b / (2 * a)
    cmass_min = poly(angle_min)
    print(f"Minimum at angle = {angle_min:.3f}, CoM_x = {cmass_min:.3f}")

    # Generate smooth x values for plotting the parabola
    angle_fit = np.linspace(min(angles), max(angles), 500)
    cmass_fit = poly(angle_fit)

    # Plot original data
    plt.close('all')
    plt.figure(figsize=(10, 5))
    plt.plot(angles, distances_x, marker='o', linestyle='-', label='Data')

    # Plot fitted parabola
    plt.plot(angle_fit, cmass_fit, 'r--', linewidth=2, label='Parabolic Fit')

    # Mark the minimum
    plt.plot(angle_min, cmass_min, 'ko', label=f'Min: ({angle_min:.2f}, {cmass_min:.2f})')
    plt.axvline(angle_min, color='gray', linestyle=':', alpha=0.7)

    # Labels and legend
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Distance (μm)')
    plt.title('Measured 1 mm distance in X vs Theta with Parabolic Fit')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.xlim(min(angles), max(angles))
    plt.show()    

def adjust_rotary(params, dark_field, white_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Adjusting Sample X ***')              
    angles = np.arange(params.angle_start, params.angle_end, params.angle_step)
    cmass_x = []
    for ang in angles:
        global_PVs["Rotation"].put(ang, wait=True, timeout=600.0) 
        sphere = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field) 
        cmass = util.center_of_mass(sphere)
        cmass_float = float(cmass[1])
        cmass_x.append(cmass_float)


    # Fit a parabola (2nd-degree polynomial)
    coeffs = np.polyfit(angles, cmass_x, 2)
    poly = np.poly1d(coeffs)

    # Generate smooth fit curve
    angle_fit = np.linspace(min(angles), max(angles), 500)
    cmass_fit = poly(angle_fit)

    # Find vertex (minimum point of the parabola)
    a, b, c = coeffs
    angle_min = -b / (2 * a)
    cmass_min = poly(angle_min)

    # Plot original data
    plt.close('all')
    plt.figure(figsize=(10, 5))
    plt.plot(angles, cmass_x, marker='o', linestyle='-', label='Data')

    # Plot parabola fit
    plt.plot(angle_fit, cmass_fit, 'r--', label='Parabolic Fit')

    # Plot minimum point
    plt.plot(angle_min, cmass_min, 'ko', label=f'Min: ({angle_min:.2f}, {cmass_min:.2f})')
    plt.axvline(angle_min, color='k', linestyle=':', alpha=0.5)

    # Labels and layout
    plt.xlabel('Angle (degrees)')
    plt.ylabel('Center of Mass X')
    plt.title('Center of Mass X vs Angle with Parabolic Fit')
    plt.grid(True)
    plt.legend()
    plt.xlim(min(angles), max(angles))
    plt.tight_layout()
    plt.show()


def adjust_center(params, dark_field, white_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Adjusting center ***')              
    for ang in [params.find_center_angle_start, params.find_center_angle_end]: 
        log.warning('  *** take 3 spheres angular %f deg ***' % float(ang))

        #sphere 0
        log.info('  *** sphere 0')
        log.info('  ***  *** moving rotary stage to %f deg position ***' % float(0))
        global_PVs["Rotation"].put(float(0), wait=True, timeout=600.0)            
        log.error('  ***  *** acquire sphere at %f deg position ***' % float(0))                                
        sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)    

        #sphere 1
        log.info('  *** sphere 1')
        log.info('  ***  *** moving rotary stage to %f deg position ***' % float(ang))                
        global_PVs["Rotation"].put(float(ang), wait=True, timeout=600.0)
        log.error('  ***  *** acquire sphere at %f deg position ***' % float(ang))                                 
        sphere_1 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
        
        #sphere 2
        log.info('  *** sphere 2')
        log.info('  ***  *** moving rotary stage to %f deg position ***' % float(2*ang))                                
        global_PVs["Rotation"].put(float(2*ang), wait=True, timeout=600.0)
        log.error('  ***  *** acquire sphere at %f deg position ***' % float(2*ang))                                                 
        sphere_2 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)

        # find shifts
        shift0 = phase_cross_correlation(sphere_0, sphere_1, normalization=None, upsample_factor=100)[0][1]
        shift1 = phase_cross_correlation(sphere_1, sphere_2, normalization=None, upsample_factor=100)[0][1]
        a = ang*np.pi/180
        # x=-(1/4) (d1+d2-2 d1 Cos[a]) Csc[a/2]^2,
        x = (1/4)*(shift0+shift1-2*shift0*np.cos(a))*1/np.sin(a/2)**2
        # r = 1/2 Csc[a/2]^2 Csc[a] Sqrt[(d1^2+d2^2-2 d1 d2 Cos[a]) Sin[a/2]^2]
        r = 1/2*1/np.sin(a/2)**2*1/np.sin(a)*np.sqrt(np.abs((shift0**2+shift1**2-2*shift0*shift1*np.cos(a))*np.sin(a/2)**2))
        # g = ArcCos[((-d1-d2+2 d1 Cos[a]) Sin[a])/(2 Sqrt[(d1^2+d2^2-2 d1 d2 Cos[a]) Sin[a/2]^2])]
        g = np.arccos(((-shift0-shift1+2*shift0*np.cos(a))*np.sin(a))/(2*np.sqrt(np.abs((shift0**2+shift1**2-2*shift0*shift1*np.cos(a))*np.sin(a/2)**2))))
        y = r*np.sin(g)*np.sign(shift0) 
        
        # find center of mass
        cmass_0 = util.center_of_mass(sphere_0)

        log.info('  ')        
        log.info('  *** position of the initial sphere wrt to the rotation center (%f,%f) ***' % (x,y))
        log.info('  *** center of mass for the initial sphere (%f,%f) ***' % (cmass_0[1],cmass_0[0]))
        log.info('  *** moving sphere to the position of the rotation center ***')

        if(params.ask):
            if util.yes_or_no('   *** Yes or No'):                
                move_center(params, cmass_0, x, y)
                check_center(params, white_field, dark_field)
            else:
                log.warning(' No motion ')
                exit()

        else:
            move_center(params, cmass_0, x, y)
            check_center(params, white_field, dark_field)


def check_center2(params, dark_field, white_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Adjusting center ***')              
    log.info('  ***  *** moving rotary stage to %f deg position ***' % float(0))
    global_PVs["Rotation"].put(float(0), wait=True, timeout=600.0)            
    log.error('  ***  *** acquire sphere at %f deg position ***' % float(0))                                
    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)    

    ang = 180
    log.info('  *** sphere 1')
    log.info('  ***  *** moving rotary stage to %f deg position ***' % float(ang))                
    global_PVs["Rotation"].put(float(ang), wait=True, timeout=600.0)
    log.error('  ***  *** acquire sphere at %f deg position ***' % float(ang))                                 
    sphere_1 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
    
    shift0 = phase_cross_correlation(sphere_0, sphere_1, normalization=None, upsample_factor=100)[0][1]
    
    log.info('  ')        
    log.info('  *** rotation axis shift in pixels' % (shift0))
    log.info('  *** rotation axis shift in mm' % (shift0*params.image_pixel_size/1000))
    

def move_center(params, cmass_0, x, y):

    global_PVs = pv.init_general_PVs(params)

    log.info('  *** moving sample top X to the rotation center ***')
    global_PVs["SampleXTop"].put(global_PVs["SampleXTop"].get()+x*params.image_pixel_size/1000, wait=True, timeout=5.0)
    log.info('  *** moving sample top Z to the rotation center ***')
    global_PVs["SampleZTop"].put(global_PVs["SampleZTop"].get()+y*params.image_pixel_size/1000, wait=True, timeout=5.0)
    log.info('  *** moving rotation center to the detector center ***')
    global_PVs["SampleX"].put(global_PVs["SampleX"].get()-(cmass_0[1]-x-global_PVs['Cam1SizeX'].get()/2)*params.image_pixel_size/1000, wait=True, timeout=600.0)

 

def check_center(params, white_field, dark_field):

    global_PVs = pv.init_general_PVs(params)

    log.warning('  *** CHECK center of mass for the centered sphere')

    log.info('  *** moving rotary stage to %f deg position ***' % float(0))
    global_PVs["Rotation"].put(float(0), wait=True, timeout=600.0)
    log.info('  *** acquire sphere at %f deg position ***' % float(0))

    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)                   
    cmass_0 = util.center_of_mass(sphere_0)
    log.warning('  *** center of mass for the centered sphere at 0 deg: [%f,%f] ***' % (cmass_0[1],cmass_0[0]))


def adjust_roll(params, dark_field, white_field, angle_shift):

    # angle_shift is the correction that is needed to apply to the rotation axis position
    # to align the Z stage on top of the rotary stage with the beam

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Adjusting roll ***')
    log.info('  *** moving rotary stage to %f deg position ***' % float(0+angle_shift))                                                
    global_PVs["Rotation"].put(float(0+angle_shift), wait=True, timeout=600.0)    
    log.info('  *** moving sphere to the detector border ***')                                                
    global_PVs["SampleXTop"].put(global_PVs["SampleXTop"].get()+global_PVs['Cam1SizeX'].get()/2*params.image_pixel_size/1000-((SPHERE_DIAMETER / 2) + GAP), wait=True, timeout=600.0)
    log.info('  *** acquire sphere at %f deg position ***' % float(0+angle_shift)) 
    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)       
    log.info('  *** moving rotary stage to %f deg position ***' % float(180+angle_shift))                                                            
    global_PVs["Rotation"].put(float(180+angle_shift), wait=True, timeout=600.0)            
    log.info('  *** acquire sphere at %f deg position ***' % float(180+angle_shift)) 
    sphere_180 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)

    cmass_0 = util.center_of_mass(sphere_0)
    cmass_180 = util.center_of_mass(sphere_180)          
    log.info('  *** center of mass for the sphere at 0 deg (%f,%f) ***' % (cmass_0[1],cmass_0[0]))
    log.info('  *** center of mass for the sphere at 180 deg (%f,%f) ***' % (cmass_180[1],cmass_180[0]))
  
    roll = np.rad2deg(np.arctan((cmass_180[0] - cmass_0[0]) / (cmass_180[1] - cmass_0[1])))
    log.warning('  *** found roll error: %f' % roll)

    log.info('  *** moving rotary stage to %f deg position ***' % float(0+angle_shift))                                                            
    global_PVs["Rotation"].put(float(0+angle_shift), wait=True, timeout=600.0)    
    log.info('  *** moving sphere back to the detector center ***')                                                            
    global_PVs["SampleXTop"].put(global_PVs["SampleXTop"].get()-(global_PVs['Cam1SizeX'].get()/2*params.image_pixel_size/1000-((SPHERE_DIAMETER / 2) + GAP)), wait=True, timeout=600.0)
    
    log.info('  *** find shifts resulting by the roll change ***')                                                            
    log.info('  *** acquire sphere at the current roll position ***')             
    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)           

    ang = roll/2 # if roll is too big then ang should be decreased to keep the sphere in the field of view
    log.info('  *** acquire sphere after testing roll change %f ***' % float(global_PVs["SampleRoll"].get()+ang))                                     
    global_PVs["SampleRoll"].put(global_PVs["SampleRoll"].get()+ang, wait=True, timeout=600.0)
    sphere_1 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)

    shift0 = phase_cross_correlation(sphere_1, sphere_0, normalization=None, upsample_factor=100)[0][1]            
    shift1 = shift0*np.sin(roll)*(np.cos(roll)*1/np.tan(ang)+np.sin(roll))
    log.info('  *** the testing roll change corresponds to %f shift in x, calculated resulting roll change gives %f shift in x ***' % (shift0,shift1))             
    log.warning('  *** change roll to %f ***' % float(global_PVs["SampleRoll"].get()+roll-ang))
    global_PVs["SampleRoll"].put(global_PVs["SampleRoll"].get()+roll-ang, wait=True, timeout=600.0)
    log.info('  *** moving sphere to the detector center ***')
    global_PVs["SampleX"].put(global_PVs["SampleX"].get()-shift1*params.image_pixel_size/1000, wait=True, timeout=600.0)
    

    log.info('  *** TEST: acquire sphere at %f deg position ***' % float(0+angle_shift)) 
    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)                   
    cmass_0 = util.center_of_mass(sphere_0)
    log.info('  *** TEST: center of mass for the sphere at 0 deg (%f,%f) ***' % (cmass_0[1],cmass_0[0]))


def adjust_pitch(params, dark_field, white_field, angle_shift):

    global_PVs = pv.init_general_PVs(params)
    
    log.warning(' *** Adjusting pitch ***')              
    log.info('  *** acquire sphere after moving it along the beam axis by 1mm ***')             
    global_PVs["SampleZTop"].put(global_PVs["SampleZTop"].get()-1.0, wait=True, timeout=600.0)            

    log.info('  *** moving rotary stage to %f deg position ***' % float(0+angle_shift))                                                            
    global_PVs["Rotation"].put(float(0+angle_shift), wait=True, timeout=600.0)                
    log.info('  *** acquire sphere at %f deg position ***' % float(0+angle_shift))             
    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)         

    log.info('  *** moving rotary stage to %f deg position ***' % float(0+angle_shift))                                                            
    global_PVs["Rotation"].put(float(180+angle_shift), wait=True, timeout=600.0)            
    log.info('  *** acquire sphere at %f deg position ***' % float(180+angle_shift))             
    sphere_180 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)

    cmass_0 = util.center_of_mass(sphere_0)            
    cmass_180 = util.center_of_mass(sphere_180)   
    log.info('  *** center of mass for the initial sphere (%f,%f) ***' % (cmass_0[1],cmass_0[0]))
    log.info('  *** center of mass for the shifted sphere (%f,%f) ***' % (cmass_180[1],cmass_180[0]))                                 
    pitch = np.rad2deg(np.arctan((cmass_180[0] - cmass_0[0])*params.image_pixel_size/1000 / 2.0))
    log.warning('  *** found pitch error: %f' % pitch)
    log.info('  *** acquire sphere back along the beam axis by -1mm ***')             
    global_PVs["SampleZTop"].put(global_PVs["SampleZTop"].get()+1.0, wait=True, timeout=600.0)
    log.warning('  *** change pitch to %f ***' % float(global_PVs["SamplePitch"].get()-pitch))             
    global_PVs["SamplePitch"].put(global_PVs["SamplePitch"].get()-pitch, wait=True, timeout=600.0)
    global_PVs["Rotation"].put(float(0+angle_shift), wait=True, timeout=600.0)    
    
    log.info('  *** TEST: acquire sphere at %f deg position ***' % float(0+angle_shift)) 
    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)                   
    cmass_0 = util.center_of_mass(sphere_0)
    log.info('  *** TEST: center of mass for the sphere at 0 deg (%f,%f) ***' % (cmass_0[1],cmass_0[0]))            


def find_resolution(params, dark_field, white_field, angle_shift):

    global_PVs = pv.init_general_PVs(params)

    log.warning(' *** Find resolution ***')
    log.info('  *** moving rotary stage to %f deg position ***' % float(0+angle_shift))                                                            
    global_PVs["Rotation"].put(float(0+angle_shift), wait=True, timeout=600.0)    
    log.info('  *** First image at X: %f mm' % (params.sample_in_x))
    log.info('  *** acquire first image')

    sphere_0 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
    plt.imshow(sphere_0,cmap='gray')
    plt.colorbar()
    # plt.show()
    second_image_x_position = params.sample_in_x + params.off_axis_position
    log.info('  *** Second image at X: %f mm' % (second_image_x_position))
    global_PVs["SampleX"].put(second_image_x_position, wait=True, timeout=600.0)
    log.info('  *** acquire second image')
    sphere_1 = util.normalize(detector.take_image(global_PVs, params), white_field, dark_field)
    plt.imshow(sphere_1,cmap='gray')
    plt.colorbar()
    # plt.show()
    plt.imshow(sphere_1-sphere_0,cmap='gray')
    plt.colorbar()
    # plt.show()


    plt.imshow(white_field,cmap='gray')
    plt.colorbar()
    # plt.show()
    plt.imshow(dark_field,cmap='gray')    
    plt.colorbar()
    # plt.show()     

    import tifffile
    tifffile.imwrite('/home/beams/2BMB/sphere_0.tiff',sphere_0)   
    tifffile.imwrite('/home/beams/2BMB/sphere_1.tiff',sphere_1)   
    
    
    log.info('  *** moving X stage back to %f mm position' % (params.sample_in_x))
    pv.move_sample_in(global_PVs, params)

    shift = phase_cross_correlation(sphere_0, sphere_1, normalization=None, upsample_factor=100)
    print(shift)
    log.info('  *** shift X: %f, Y: %f' % (shift[0][1],shift[0][0]))
    image_pixel_size =  abs(params.off_axis_position) / np.linalg.norm(shift[0]) * 1000.0
    
    log.warning('  *** found resolution %f μm/pixel' % (image_pixel_size))    
    params.image_pixel_size = image_pixel_size
          
    global_PVs['ImagePixelSize'].put(params.image_pixel_size, wait=True)


def adjust_focus(params):
    
    global_PVs = pv.init_general_PVs(params)

    step = 0.05
    
    direction = 1
    max_std = 0
    three_std = np.ones(3)*2**16
    cnt = 0
    decrease_step = False
    while(step>0.0001):
        initpos = global_PVs['Focus'].get()
        curpos = initpos + step*direction
        global_PVs['Focus'].put(curpos, wait=True, timeout=600.0)
        img = detector.take_image(global_PVs, params)        
        cur_std = np.std(img)
        log.info('  ***   *** Positon: %f Standard deviation: %f ' % (curpos,cur_std))
        if(cur_std > max_std): # store max std
            max_std = cur_std
        three_std[np.mod(cnt,3)] = cur_std # store std for 3 last measurements 
        if(np.sum(three_std<max_std)==3):# pass a peak
            direction = -direction
            if(decrease_step):# decrease focusing motor step
                step/=2
            else:#do not decrease step for the first direction change
                decrease_step = True
            three_std = np.ones(3)*2**16
            max_std = 0
            log.warning('  *** change direction and step to %f' % (step))
        cnt+=1

    log.warning('  *** Focusing done')

    return

