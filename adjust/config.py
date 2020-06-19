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
adjust config file
"""

import os
import sys
import shutil
import pathlib
import argparse
import configparser
import h5py
import numpy as np

from collections import OrderedDict

from adjust import log
from adjust import util
from adjust import __version__

home = os.path.expanduser("~")
LOGS_HOME = os.path.join(home, 'logs')
CONFIG_FILE_NAME = os.path.join(home, 'adjust.conf')

SECTIONS = OrderedDict()

SECTIONS['general'] = {
    'config': {
        'default': CONFIG_FILE_NAME,
        'type': str,
        'help': "File name of configuration file",
        'metavar': 'FILE'},
    'logs-home': {
        'default': LOGS_HOME,
        'type': str,
        'help': "Log file directory",
        'metavar': 'FILE'},
    'verbose': {
        'default': False,
        'help': 'Verbose output',
        'action': 'store_true'},
    'ask': {
        'default': False,
        'help': ' ',
        'action': 'store_true'},
    'testing': {
        'default': False,
        'help': ' ',
        'action': 'store_true'},
        }


SECTIONS['epics-pvs'] = {
    'shutter-open-pv-name':{
        'default': '2bma:A_shutter:open',
        'type': str,
        'help': 'shutter open pv name'},
    'shutter-close-pv-name':{
        'default': '2bma:A_shutter:close',
        'type': str,
        'help': 'shutter close pv name'},
    'shutter-status-pv-name':{
        'default': 'PA:02BM:STA_A_FES_OPEN_PL',
        'type': str,
        'help': 'shutter status pv name'},
    'sample-x-pv-name':{
        'default': '2bma:m49',
        'type': str,
        'help': 'sample x pv name'},
    'sample-y-pv-name':{
        'default': '2bma:m20',
        'type': str,
        'help': 'sample y pv name'},
    'rotation-pv-name':{
        'default': '2bmb:m82',
        'type': str,
        'help': 'rotation pv name'},
    'sample-x-center-pv-name':{
        'default': '2bmS1:m2',
        'type': str,
        'help': 'sample x center pv name'},
    'sample-z-center-pv-name':{
        'default': '2bmS1:m1',
        'type': str,
        'help': 'sample z center pv name'},
    'sample-pitch-pv-name':{
        'default': '2bma:m50',
        'type': str,
        'help': 'sample pitch pv name'},
    'sample-roll-pv-name':{
        'default': '2bma:m51',
        'type': str,
        'help': 'sample roll pv name'},
    'focus-pv-name':{
        'default': '2bma:m41',
        'type': str,
        'help': 'focus pv name'},
    'image-pixel-size-pv-name':{
        'default': '2bma:TomoScan:ImagePixelSize',
        'type': str,
        'help': 'image pixel sizef pv name'},
        }

SECTIONS['shutter'] = {
    'shutter-close-value':{
        'default': '1',
        'type': int,
        'help': 'value to set the shutter-close-pv-name to close the shutter'},
    'shutter-open-value':{
        'default': '1',
        'type': int,
        'help': 'value to set the shutter-open-pv-name to open the shutter'},
    'shutter-status-open-value':{
        'default': '1',
        'type': int,
        'help': 'shutter open status value'},
    'shutter-status-close-value':{
        'default': '0',
        'type': int,
        'help': 'shutter close status value'},
        }

SECTIONS['detector'] = {
    'detector-prefix':{
        'default': '2bmbSP1:',
        'type': str,
        'help': ''},
    'exposure-time': {
        'default': 0.1,
        'type': float,
        'help': " "},
    'image-pixel-size': {
        'default': None,
        'type': float,
        'help': "Detector pixel size in micron/pixel"},
         }

SECTIONS['sample-motion'] = {
    'sample-in-x': {
        'default': 0,
        'type': float,
        'help': "Sample position during data collection"},
    'sample-out-x': {
        'default': 3,
        'type': float,
        'help': "Sample position for white field images"},
    'sample-in-y': {
        'default': 0,
        'type': float,
        'help': "Sample position during data collection"},
    'sample-out-y': {
        'default': 3,
        'type': float,
        'help': "Sample position for white field images"},
    'flat-field-axis': {
        'choices': ['horizontal', 'vertical', 'both'],
        'default': 'horizontal',
        'type': str,
        'help': " "},
        }

SECTIONS['sphere'] = {
   'rotation-axis-location': {
        'default': None,
        'type': float,
        'help': "horizontal location of the rotation axis (pixels)"},
    'rotation-axis-roll': {
        'default': None,
        'type': float,
        'help': "rotation axis roll "},
    'rotation-axis-pitch': {
        'default': None,
        'type': float,
        'help': "rotation axis pitch"},
    'off-axis-position': {
        'default': 0.1,
        'type': float,
        'help': "Off axis horizontal position of the sphere used to calculate resolution (mm)"},
    }

SECTIONS['adjust'] = {
    'adjust-center-angle-1': {
        'default': 10,
        'type': float,
        'help': "Adjust center first angle (deg)"},
    'adjust-center-angle-2': {
        'default': 45,
        'type': float,
        'help': "Adjust center second angle (deg)"},
    }


SPHERE_PARAMS = ('epics-pvs', 'shutter', 'detector', 'sample-motion', 'sphere', 'adjust')
NICE_NAMES = ('general', 'epics-pvs', 'shutter', 'detector', 'sample-motion', 'sphere', 'adjust')


def get_config_name():
    """Get the command line --config option."""
    name = CONFIG_FILE_NAME
    for i, arg in enumerate(sys.argv):
        if arg.startswith('--config'):
            if arg == '--config':
                return sys.argv[i + 1]
            else:
                name = sys.argv[i].split('--config')[1]
                if name[0] == '=':
                    name = name[1:]
                return name

    return name


def parse_known_args(parser, subparser=False):
    """
    Parse arguments from file and then override by the ones specified on the
    command line. Use *parser* for parsing and is *subparser* is True take into
    account that there is a value on the command line specifying the subparser.
    """
    if len(sys.argv) > 1:
        subparser_value = [sys.argv[1]] if subparser else []
        config_values = config_to_list(config_name=get_config_name())
        values = subparser_value + config_values + sys.argv[1:]
        #print(subparser_value, config_values, values)
    else:
        values = ""

    return parser.parse_known_args(values)[0]


def config_to_list(config_name=CONFIG_FILE_NAME):
    """
    Read arguments from config file and convert them to a list of keys and
    values as sys.argv does when they are specified on the command line.
    *config_name* is the file name of the config file.
    """
    result = []
    config = configparser.ConfigParser()

    if not config.read([config_name]):
        return []

    for section in SECTIONS:
        for name, opts in ((n, o) for n, o in SECTIONS[section].items() if config.has_option(section, n)):
            value = config.get(section, name)

            if value is not '' and value != 'None':
                action = opts.get('action', None)

                if action == 'store_true' and value == 'True':
                    # Only the key is on the command line for this action
                    result.append('--{}'.format(name))

                if not action == 'store_true':
                    if opts.get('nargs', None) == '+':
                        result.append('--{}'.format(name))
                        result.extend((v.strip() for v in value.split(',')))
                    else:
                        result.append('--{}={}'.format(name, value))

    return result
   

class Params(object):
    def __init__(self, sections=()):
        self.sections = sections + ('general', )

    def add_parser_args(self, parser):
        for section in self.sections:
            for name in sorted(SECTIONS[section]):
                opts = SECTIONS[section][name]
                parser.add_argument('--{}'.format(name), **opts)

    def add_arguments(self, parser):
        self.add_parser_args(parser)
        return parser

    def get_defaults(self):
        parser = argparse.ArgumentParser()
        self.add_arguments(parser)

        return parser.parse_args('')


def write(config_file, args=None, sections=None):
    """
    Write *config_file* with values from *args* if they are specified,
    otherwise use the defaults. If *sections* are specified, write values from
    *args* only to those sections, use the defaults on the remaining ones.
    """
    config = configparser.ConfigParser()
    for section in SECTIONS:
        config.add_section(section)
        for name, opts in SECTIONS[section].items():
            if args and sections and section in sections and hasattr(args, name.replace('-', '_')):
                value = getattr(args, name.replace('-', '_'))
                if isinstance(value, list):
                    # print(type(value), value)
                    value = ', '.join(value)
            else:
                value = opts['default'] if opts['default'] is not None else ''

            prefix = '# ' if value is '' else ''

            if name != 'config':
                config.set(section, prefix + name, str(value))


    with open(config_file, 'w') as f:
        config.write(f)


def write_hdf(args=None, sections=None):
    """
    Write in the hdf raw data file the content of *config_file* with values from *args* 
    if they are specified, otherwise use the defaults. If *sections* are specified, 
    write values from *args* only to those sections, use the defaults on the remaining ones.
    """
    if (args == None):
        log.warning("  *** Not saving log data to the HDF file.")

    else:
        hdf_fname = args.file_path + os.sep + args.file_name + '.h5'

        with h5py.File(hdf_fname,'r+') as hdf_file:
            #If the group we will write to already exists, remove it
            if hdf_file.get('/process/acquisition/tomo-scan-2bm-' + __version__):
                del(hdf_file['/process/acquisition/tomo-scan-2bm-' + __version__])
            #dt = h5py.string_dtype(encoding='ascii')
            log.info("  *** tomopy.conf parameter written to /process/acquisition/tomo-scan-2bm-%s in file %s " % (__version__, args.file_name))
            config = configparser.ConfigParser()
            for section in SECTIONS:
                config.add_section(section)
                for name, opts in SECTIONS[section].items():
                    if args and sections and section in sections and hasattr(args, name.replace('-', '_')):
                        value = getattr(args, name.replace('-', '_'))
                        if isinstance(value, list):
                            # print(type(value), value)
                            value = ', '.join(value)
                    else:
                        value = opts['default'] if opts['default'] is not None else ''

                    prefix = '# ' if value is '' else ''

                    if name != 'config':
                        dataset = '/process' + '/acquisition/tomo-scan-2bm-' + __version__ + '/' + section + '/'+ name
                        dset_length = len(str(value)) * 2 if len(str(value)) > 5 else 10
                        dt = 'S{0:d}'.format(dset_length)
                        hdf_file.require_dataset(dataset, shape=(1,), dtype=dt)
                        log.info(name + ': ' + str(value))
                        try:
                            hdf_file[dataset][0] = np.string_(str(value))
                        except TypeError:
                            print(value)
                            raise TypeError


def show_configs(args):
    """Log all values set in the args namespace.

    Arguments are grouped according to their section and logged alphabetically
    using the DEBUG log level thus --verbose is required.
    """
    args = args.__dict__

    log.warning('tomo scan status start')
    for section, name in zip(SECTIONS, NICE_NAMES):
        entries = sorted((k for k in args.keys() if k.replace('_', '-') in SECTIONS[section]))

        # print('show_configs', section, name, entries)
        if entries:
            log.info(name)

            for entry in entries:
                value = args[entry] if args[entry] is not None else "-"
                log.info("  {:<16} {}".format(entry, value))

    log.warning('tomo scan status end')


def update_sphere(args):
       # update adjust.conf
        sections = SPHERE_PARAMS
        write(args.config, args=args, sections=sections)
