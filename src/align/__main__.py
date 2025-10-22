#!/usr/bin/env python

# #########################################################################
# Copyright (c) 2019-2020, UChicago Argonne, LLC. All rights reserved.    #
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
Automatic determinato of the detector pixel size, focus, alignment rotation axis tilt/pitch and finding center the rotation axis in the middle of the detector field of view.  .
"""

import os
import sys
import argparse

from datetime import datetime

from align import config, __version__
from align import log
from align import sphere
from align import stick
from align import sample


def init(args):

    if not os.path.exists(str(args.config)):
        config.write(args.config)
    else:
        log.warning("{0} already exists".format(args.config))

def run_status(args):
    config.show_configs(args)

def run_sample_resolution(args):
    sample.adjust('resolution', args)

def run_sample_rotation(args):
    sample.adjust('center', args)


# OLD pre-hexapod pre-APS-U routines
def run_resolution(args):
    sphere.adjust('resolution', args)

def run_focus(args):
    sphere.adjust('focus', args)

def run_pitch(args):
    sphere.adjust('pitch', args)

def run_roll(args):
    sphere.adjust('roll', args)

def run_stick_roll(args):
    stick.adjust('roll', args)

def run_rotary(args):
    sphere.adjust('rotary', args)

def run_theta(args):
    sphere.adjust('theta', args)

def run_center(args):
    sphere.adjust('center', args)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', **config.SECTIONS['general']['config'])
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))

    sphere_params = config.SPHERE_PARAMS
    rotary_params = config.ROTARY_PARAMS
    theta_params  = config.THETA_PARAMS
    
    cmd_parsers = [
        ('init',                init,                  (),                            "Create configuration file"),
        ('status',             run_status,            sphere_params,                  "Show the align cli status"),
        ('resolution',         run_sample_resolution, sphere_params,                  "Find the image resolution"),
        ('rotation',           run_sample_rotation,   sphere_params,                  "Align rotation axis"),
        ('old_resolution',     run_resolution,        sphere_params,                  "Find the image resolution"),
        ('old_focus',          run_focus,             sphere_params,                  "Find the scintillator focus"),
        ('old_center',         run_center,            sphere_params,                  "Find rotation axis center"),
        ('old_pitch',          run_pitch,             sphere_params,                  "Align rotation axis pitch"),
        ('old_roll',           run_roll,              sphere_params,                  "Align rotation axis roll"),
        ('old_sroll',          run_stick_roll,        sphere_params,                  "Align rotation axis roll with a stick"),
        ('old_rotary',         run_rotary,            rotary_params,                  "Align rotary stage to be orthogonal to the beam"),
        ('old_theta',          run_theta,             theta_params,                   "Align theta stage to be orthogonal to the beam"),
    ]

    subparsers = parser.add_subparsers(title="Commands", metavar='')

    for cmd, func, sections, text in cmd_parsers:
        cmd_params = config.Params(sections=sections)
        cmd_parser = subparsers.add_parser(cmd, help=text, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cmd_parser = cmd_params.add_arguments(cmd_parser)
        cmd_parser.set_defaults(_func=func)

    args = config.parse_known_args(parser, subparser=True)

    # create logger
    logs_home = args.logs_home

    # make sure logs directory exists
    if not os.path.exists(logs_home):
        os.makedirs(logs_home)

    lfname = os.path.join(logs_home, 'adjust_' + datetime.strftime(datetime.now(), "%Y-%m-%d_%H_%M_%S") + '.log')
 
    log.setup_custom_logger(lfname)
    log.info("Saving log at %s" % lfname)

    try:
        # config.show_configs(args)
        args._func(args)
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()

