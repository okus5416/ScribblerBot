# Copyright 2014 Mitchell Kember. Subject to the MIT License.

"""Mediates between the server and the currently executing program."""

import json

from gevent import Greenlet, sleep
from gevent.queue import Empty, Queue

from scribbler.programs import avoider, calib, tracie


# Map program IDs to their respective classes or functions.
PROGRAMS = {
    'avoid': avoider.Avoider,
    'calib': calib.Calib,
    'tracie': tracie.Tracie
}

# This is the program that is initially active.
DEFAULT_PROGRAM = 'tracie'

# The prefix to a command which indicates a program switch.
PROGRAM_PREFIX = 'program:'

# Amount of time to sleep between main loop iterations (seconds).
LOOP_DELAY = 0.01

# Amount of time to delay before starting (seconds), to ensure that the starting
# message gets sent before the program's first status update.
START_DELAY = 0.1

# Timeout for status queue long-polling (seconds). This should be less than
# `ajaxTimeout` in `controls.js`, so that the server times out just before the
# client gives up, and the server responds with a non-200 status.
STATUS_POLL_TIMEOUT = 25


class Controller(object):

    """Manages a program's main loop in a Greenlet."""

    def __init__(self, program_id=DEFAULT_PROGRAM):
        """Creates a controller to control the specified program. The program
        doesn't start executing until the start method is called."""
        self.messages = Queue()
        self.program_id = program_id
        self.program = PROGRAMS[program_id]()
        self.green = None
        self.can_reset = False

    def start(self):
        """Starts (or resumes) the execution of the program."""
        self.green = Greenlet(self.main_loop)
        self.green.start_later(START_DELAY)
        self.program.start()
        self.can_reset = True

    def stop(self):
        """Stops the execution of the program."""
        self.program.stop()
        if self.green:
            self.green.kill()

    def reset(self):
        """Stops the program and resets it to its initial state."""
        self.stop()
        self.program.reset()
        self.can_reset = False

    def switch_program(self, program_id):
        """Stops execution and switches to a new program."""
        self.stop()
        self.program_id = program_id
        self.program = PROGRAMS[program_id]()
        self.can_reset = False

    def main_loop(self):
        """Runs the program's loop method continously, collecting any returned
        messages into the messages queue."""
        while True:
            msg = self.program.loop()
            if msg:
                self.messages.put(msg)
            sleep(LOOP_DELAY)

    def __call__(self, command):
        """Accepts a command and either performs the desired action or passes
        the message on to the program. Returns a status message."""
        if command == 'short:sync':
            pid = self.program_id
            running = bool(self.green)
            can_reset = self.can_reset
            return "{} {} {}".format(pid, running, can_reset)
        if command == 'short:param-help':
            return json.dumps(self.program.codes)
        if command == 'long:status':
            try:
                msg = self.messages.get(timeout=STATUS_POLL_TIMEOUT)
            except Empty:
                return None
            return msg
        if command.startswith(PROGRAM_PREFIX):
            prog = command[len(PROGRAM_PREFIX):]
            self.switch_program(prog)
            return "switched to {}".format(prog)
        if command == 'control:start':
            reason = self.program.no_start()
            if reason:
                return reason
            if self.green:
                return "already running"
            self.start()
            return "program resumed"
        if command == 'control:stop':
            if not self.green:
                return "not running"
            self.stop()
            return "program paused"
        if command == 'control:reset':
            self.reset()
            return "program reset"
        return self.program(command)
