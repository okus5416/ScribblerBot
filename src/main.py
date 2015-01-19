#!/usr/bin/env python

# Copyright 2014 Mitchell Kember. Subject to the MIT License.

from __future__ import print_function

import argparse
import os
import sys
import __builtin__

from scribbler.server import Server

import template


# Description for the usage message.
DESC = "Starts the Scribbler Bot server."

# All web resources are in the public folder.
PUBLIC = '../public'

# Requests for any paths other than these will 404.
WHITELIST = [
    '/', '/index.html', '/404.html', '/style.css',
    '/controls.js', '/drawing.js'
]

# Configure the arguments.
parser = argparse.ArgumentParser(description=DESC)
parser.add_argument(
    '-n',
    '--nobrowser',
    action='store_true',
    help="don't open the browser"
)
parser.add_argument(
    '-s',
    '--host',
    type=str,
    default='localhost',
    help='serve on this host'
)
parser.add_argument(
    '-p',
    '--port',
    type=int,
    default=8080,
    help="serve on this port"
)
parser.add_argument(
    '-b',
    '--bluetooth',
    type=str,
    default='/dev/tty.Fluke2-0530-Fluke2',
    help="the Scribbler is on this Bluetooth serial port"
)
parser.add_argument(
    '-d',
    '--dummymyro',
    action='store_true',
    help="use a dummy Myro library"
)

# Go to this directory to make the relative paths work.
script_dir = os.path.dirname(sys.argv[0])
if script_dir:
    os.chdir(script_dir)

# Parse the command-line arguments.
args = parser.parse_args()

# Generate the HTML from the templates.
template.generate()

# Make sure they are all there.
if any([not os.path.exists(PUBLIC + p) for p in WHITELIST]):
    print("error: missing files in /public", file=sys.stderr)
    sys.exit(1)

# Import Myro, or the dummy version.
if args.dummymyro:
    import scribbler.programs.nomyro as myro
else:
    import myro

# This is an ugly hack. I know.
__builtin__.myro = myro

# Start Myro
myro.initialize(args.bluetooth)

# Start the server.
server = Server(args.host, args.port, PUBLIC, WHITELIST)
server.start(not args.nobrowser)
server.stay_alive()
