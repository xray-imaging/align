======
adjust
======

**adjust** is commad-line-interface to automatically determine the detector pixel size, to adjust focus, to align rotation axis tilt/pitch and to center the rotation axis in the middle of the detector field of view.  

Installation
============

::

    $ git clone https://github.com/xray-imaging/adjust.git
    $ cd adjust
    $ python setup.py install

in a prepared virtualenv or as root for system-wide installation.

.. warning::
    If your python installation is in a location different from #!/usr/bin/env python please edit the first line of the bin/adjust file to match yours.

Usage
=====

::

    $ adjust resolution
    $ adjust focus
    $ adjust center
    $ adjust roll
    $ adjust pitch

to list of all available options::

    $ adjust  -h


Configuration File
------------------

adjust parameters are stored in **adjust.conf**. You can create a template with::

    $ adjust init

**adjust.conf** is constantly updated to keep track of the last stored parameters, as initalized by **init** or modified by setting a new option value. 

Beamline customization
======================

To run **adjust** on a different beamline you need to change the EPICS pv names associated to your instrument. This can be done at run time by setting::

    --focus-pv-name FOCUS_PV_NAME
                        focus pv name (default: 2bma:m41)
    --image-pixel-size-pv-name IMAGE_PIXEL_SIZE_PV_NAME
                image pixel sizef pv name (default:
                2bma:TomoScan:ImagePixelSize)
    --rotation-pv-name ROTATION_PV_NAME
                rotation pv name (default: 2bma:m82)
    --sample-pitch-pv-name SAMPLE_PITCH_PV_NAME
                sample pitch pv name (default: 2bma:m50)
    --sample-roll-pv-name SAMPLE_ROLL_PV_NAME
                sample roll pv name (default: 2bma:m51)
    --sample-x-center-pv-name SAMPLE_X_CENTER_PV_NAME
                sample x center pv name (default: 2bmS1:m2)
    --sample-x-pv-name SAMPLE_X_PV_NAME
                sample x pv name (default: 2bma:m49)
    --sample-y-pv-name SAMPLE_Y_PV_NAME
                sample y pv name (default: 2bma:m20)
    --sample-z-center-pv-name SAMPLE_Z_CENTER_PV_NAME
                sample z center pv name (default: 2bmS1:m1)
    --shutter-close-pv-name SHUTTER_CLOSE_PV_NAME
                shutter close pv name (default: 2bma:A_shutter:close)
    --shutter-open-pv-name SHUTTER_OPEN_PV_NAME
                shutter open pv name (default: 2bma:A_shutter:open)
    --shutter-status-pv-name SHUTTER_STATUS_PV_NAME
                shutter status pv name (default:
            PA:02BM:STA_A_FES_OPEN_PL)
    --shutter-close-value SHUTTER_CLOSE_VALUE
                value to set the shutter-close-pv-name to close the
                shutter (default: 1)
    --shutter-open-value SHUTTER_OPEN_VALUE
                value to set the shutter-open-pv-name to open the
                shutter (default: 1)
    --shutter-status-close-value SHUTTER_STATUS_CLOSE_VALUE
                shutter close status value (default: 0)
    --shutter-status-open-value SHUTTER_STATUS_OPEN_VALUE
                shutter open status value (default: 1)
    --detector-prefix DETECTOR_PREFIX

or by changing the default pv_name values in the adjust/config.py file
