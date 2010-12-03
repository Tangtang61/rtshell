#!/usr/bin/env python
# -*- Python -*-
# -*- coding: utf-8 -*-

'''rtshell

Copyright (C) 2009-2010
    Geoffrey Biggs
    RT-Synthesis Research Group
    Intelligent Systems Research Institute,
    National Institute of Advanced Industrial Science and Technology (AIST),
    Japan
    All rights reserved.
Licensed under the Eclipse Public License -v 1.0 (EPL)
http://www.opensource.org/licenses/eclipse-1.0.txt

rtstart library.

'''


import optparse
import os
import rtctree.component
import rtctree.path
import rtctree.tree
import rtsprofile.rts_profile
import sys
import traceback

import actions
import option_store
import plan
import rts_exceptions
import rtshell


def check_required_component_actions(rtsprofile):
    checks = []
    # First perform a sanity check of the system.
    # All required components must be present
    for comp in [c for c in rtsprofile.components if c.is_required]:
        checks.append(actions.CheckForRequiredCompAct(os.sep + comp.path_uri,
            comp.id, comp.instance_name,
            callbacks=[actions.RequiredActionCB()]))
    return checks


def activate_actions(rtsprofile):
    checks = check_required_component_actions(rtsprofile)

    activates = []
    for comp in [c for c in rtsprofile.components if c.is_required]:
        for ec in comp.execution_contexts:
            activates.append(actions.ActivateCompAct(os.sep + comp.path_uri,
                comp.id, comp.instance_name, ec.id,
                callbacks=[actions.RequiredActionCB()]))

    for comp in [c for c in rtsprofile.components if not c.is_required]:
        for ec in comp.execution_contexts:
            activates.append(actions.ActivateCompAct(os.sep + comp.path_uri,
                comp.id, comp.instance_name, ec.id))

    return checks, activates


def start(profile=None, xml=True, dry_run=False, tree=None):
    # Load the profile
    if profile:
        # Read from a file
        with open(args[0]) as f:
            if options.xml:
                rtsp = rtsprofile.rts_profile.RtsProfile(xml_spec=f)
            else:
                rtsp = rtsprofile.rts_profile.RtsProfile(yaml_spec=f)
    else:
        # Read from standard input
        lines = sys.stdin.read()
        if options.xml:
            rtsp = rtsprofile.rts_profile.RtsProfile(xml_spec=lines)
        else:
            rtsp = rtsprofile.rts_profile.RtsProfile(yaml_spec=lines)

    # Build a list of actions to perform that will start the system
    checks, activates = activate_actions(rtsp)
    plan = plan.Plan()
    plan.make(rtsp, activates, rtsp.activation,
            rtctree.component.Component.ACTIVE)
    if options.dry_run:
        for a in checks:
            print a
        print plan
    else:
        if not tree:
            # Load the RTC Tree, using the paths from the profile
            tree = rtctree.tree.create_rtctree(paths=[rtctree.path.parse_path(
                os.sep + c.path_uri)[0] for c in rtsp.components])
        try:
            for a in checks:
                a(tree)
            plan.execute(tree)
        except rts_exceptions.RequiredActionFailedError:
            plan.cancel()
            raise


def main(argv=None, tree=None):
    usage = '''Usage: %prog [options] [RTSProfile specification file]
Start an RT system using an RT system profile specified in XML or YAML.

If no file is given, the profile is read from standard input.'''
    parser = optparse.OptionParser(usage=usage, version=rtshell.RTSH_VERSION)
    parser.add_option('--dry-run', dest='dry_run', action='store_true',
            default=False, help="Print what will be done but don't actually '\
            'do anything. [Default: %default]")
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
            default=False,
            help='Output verbose information. [Default: %default]')
    parser.add_option('-x', '--xml', dest='xml', action='store_true',
            default=True, help='Use XML input format. [Default: True]')
    parser.add_option('-y', '--yaml', dest='xml', action='store_false',
            help='Use YAML input format. [Default: False]')

    if argv:
        sys.argv = [sys.argv[0]] + argv
    try:
        options, args = parser.parse_args()
    except optparse.OptionError, e:
        print >>sys.stderr, 'OptionError: ', e
        return 1
    option_store.OptionStore().verbose = options.verbose

    if not args:
        profile = None
    elif len(args) == 1:
        profile = args[0]
    else:
        print >>sys.stderr, usage
        return 1

    try:
        start(profile=profile, xml=options.xml, dry_run=options.dry_run,
                tree=tree)
    except Exception, e:
        if options.verbose:
            traceback.print_exc()
        print >>sys.stderr, '{0}: {1}'.format(sys.argv[0], e)
        return 1
    return 0


# vim: tw=79

