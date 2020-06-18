======
adjust
======

**adjust** is commad-line-interface for automatically determine the detector pixel size, adjust focus, align rotation axis tilt/pitch and center the rotation axis in the middle of the detector field of view.  

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

