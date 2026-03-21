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
align config file
"""

import os
import sys
import argparse
import configparser

import numpy as np

from collections import OrderedDict

from align import log

home = os.path.expanduser("~")
LOGS_HOME = os.path.join(home, 'logs')
CONFIG_FILE_NAME = os.path.join(home, 'align.conf')

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
        'default': True,
        'help': ' ',
        'action': 'store_true'},
        }

SECTIONS['epics-pvs'] = {
    'shutter-open-pv-name':{
        'default': '2bma:B_shutter:open',
        'type': str,
        'help': 'shutter open pv name'},
    'shutter-close-pv-name':{
        'default': '2bma:B_shutter:close',
        'type': str,
        'help': 'shutter close pv name'},
    'shutter-status-pv-name':{
        'default': 'PA:02BM:STA_B_SBS_OPEN_PL',
        'type': str,
        'help': 'shutter status pv name'},
    'sample-x-pv-name':{
        'default': '2bmHXP:m1',
        'type': str,
        'help': 'sample x motor pv name'},
    'sample-y-pv-name':{
        'default': '2bmHXP:m3',
        'type': str,
        'help': 'sample y motor pv name'},
    'sample-theta-pv-name':{
        'default': '2bmHXP:m6',
        'type': str,
        'help': 'sample theta motor pv name'},
    'rotation-pv-name':{
        'default': '2bmb:m102',
        'type': str,
        'help': 'sample rotation motor pv name'},
    'sample-x-top-pv-name':{
        'default': '2bmb:m17',
        'type': str,
        'help': 'sample x center motor pv name'},
    'sample-z-top-pv-name':{
        'default': '2bmb:m18',
        'type': str,
        'help': 'sample z center rmotor pv name'},
    'sample-pitch-pv-name':{
        'default': '2bmHXP:m5',
        'type': str,
        'help': 'sample pitch motor pv name'},
    'sample-roll-pv-name':{
        'default': '2bmHXP:m4',
        'type': str,
        'help': 'sample roll motor pv name'},
    'sample-lamino-pv-name':{
        'default': '2bmb:m49',
        'type': str,
        'help': 'sample lamino motor pv name'},
    'focus-lens-1-pv-name':{
        'default': '2bmb:m2',
        'type': str,
        'help': 'focus motor pv name for lens 1'},
    'focus-lens-2-pv-name':{
        'default': '2bmb:m3',
        'type': str,
        'help': 'focus motor pv name for lens 2'},
    'focus-lens-3-pv-name':{
        'default': '2bmb:m4',
        'type': str,
        'help': 'focus motor pv name for lens 3'},
    'camera-rotation-1-pv-name':{
        'default': '2bmb:m7',
        'type': str,
        'help': 'camera 1 rotation motor pv name'},
    'camera-rotation-2-pv-name':{
        'default': '2bmb:m8',
        'type': str,
        'help': 'camera 2 rotation motor pv name'},
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
        'default': '2bmSP2:',
        'type': str,
        'help': ''},
    'exposure-time': {
        'default': 0.1,
        'type': float,
        'help': " "},
   'image-pixel-size': {
        'default': None,
        'type': float,
        'help': "Image pixel size (um)"},
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
        'default': -3,
        'type': float,
        'help': "Sample position for white field images"},
    'flat-field-axis': {
        'choices': ['horizontal', 'vertical', 'both'],
        'default': 'horizontal',
        'type': str,
        'help': " "},
        }

SECTIONS['resolution'] = {
    'off-axis-position': {
        'default': 0.1,
        'type': float,
        'help': "Off axis horizontal position of the sample used to calculate resolution (mm)"},
    }

SECTIONS['tomoscan'] = {
    'tomoscan-prefix':{
        'default': '2bmb:TomoScan:',
        'type': str,
        'help': ''},
    }

SECTIONS['mctoptics'] = {
    'mctoptics-prefix':{
        'default': '2bm:MCTOptics:',
        'type': str,
        'help': ''},
    }

SAMPLE_PARAMS = ('epics-pvs', 'shutter', 'detector', 'sample-motion', 'resolution', 'tomoscan', 'mctoptics')
NICE_NAMES = ('general', 'epics-pvs', 'shutter', 'detector', 'sample-motion', 'resolution', 'tomoscan', 'mctoptics')


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
    Parse arguments from file and then override them with the ones
    specified on the command line. If *subparser* is True, detect
    the subcommand automatically so we can inject config arguments
    before it.
    """
    import difflib
    argv = sys.argv[1:]

    # Detect subcommand (first positional arg not starting with '-')
    subcmd = argv[0] if (subparser and len(argv) > 0 and not argv[0].startswith('-')) else None

    # Read args from config file
    config_values = config_to_list(config_name=get_config_name())

    # --- FIX: inject config values *after* subcommand, not before ---
    # so that subparser-level defaults don’t override them
    if subcmd:
        values = [subcmd] + config_values + argv[1:]
    else:
        values = config_values + argv
    # ---------------------------------------------------------------

    # First pass: parse using argparse's built-in method
    args, unknown = parser.parse_known_args(values)

    # -----------------------
    # Strict unknown argument detection
    # -----------------------
    valid_args = [f"--{k}" for section in SECTIONS.values() for k in section.keys()]
    known_subcommands = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            known_subcommands.extend(action.choices.keys())

    real_unknowns = []
    for u in unknown:
        if not u.startswith("--"):
            continue
        if u in known_subcommands:
            continue
        u_clean = u.split("=")[0]
        if u_clean not in valid_args:
            real_unknowns.append(u)

    if real_unknowns:
        print("ERROR: Unknown argument(s):")
        for bad in real_unknowns:
            suggestion = difflib.get_close_matches(bad.split("=")[0], valid_args, n=1)
            if suggestion:
                print(f"  {bad}  (did you mean {suggestion[0]}?)")
            else:
                print(f"  {bad}")
        sys.exit(1)

    # -----------------------
    # Missing value detection
    # -----------------------
    missing_values = []
    required_value_flags = [
        f"--{name}" for section in SECTIONS.values() for name, opts in section.items()
        if opts.get("action") != "store_true" and opts.get("nargs") in (None, 1)
    ]
    # Only check user-supplied CLI args, not config values
    user_args = argv[1:] if subcmd else argv
    for i, token in enumerate(user_args):
        if token in required_value_flags:
            if i + 1 == len(user_args) or user_args[i + 1].startswith("--"):
                missing_values.append(token)
        elif any(token.startswith(flag + "=") for flag in required_value_flags):
            continue

    if missing_values:
        print("\nERROR: Missing value(s) for argument(s):")
        for flag in missing_values:
            print(f"  {flag}")
        sys.exit(2)

    return args


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

            if value != '' and value != 'None':
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

            prefix = '# ' if value == '' else ''

            if name != 'config':
                config.set(section, prefix + name, str(value))


    with open(config_file, 'w') as f:
        config.write(f)


def show_configs(args):
    """Log all values set in the args namespace.

    Arguments are grouped according to their section and logged alphabetically
    using the DEBUG log level thus --verbose is required.
    """
    args = args.__dict__

    log.warning('align status start')
    for section, name in zip(SECTIONS, NICE_NAMES):
        entries = sorted((k for k in args.keys() if k.replace('_', '-') in SECTIONS[section]))

        # print('show_configs', section, name, entries)
        if entries:
            log.info(name)

            for entry in entries:
                value = args[entry] if args[entry] is not None else "-"
                log.info("  {:<16} {}".format(entry, value))

    log.warning('align status end')


def save_sample_params(args):
       # update align.conf
        sections = SAMPLE_PARAMS
        write(args.config, args=args, sections=sections)
