# Copyright 2014 Mitchell Kember and Charles Bai. Subject to the MIT License.

"""Calibrates the angle-to-time conversion factor."""

from scribbler.programs.base import ModeProgram


# Short codes for the parameters of the program.
PARAM_CODES = {
    'ca': 'calib_angle',
}

# Default values for the parameters of the program.
PARAM_DEFAULTS = {
    'calib_angle': 90, # deg
}


class Calib(ModeProgram):

    """Program for calibrating the `att` parameter."""

    def __init__(self):
        ModeProgram.__init__(self, 0)
        self.running = False
        self.add_params(PARAM_DEFAULTS, PARAM_CODES)

    def __call__(self, command):
        p_status = ModeProgram.__call__(self, command)
        if p_status:
            return p_status
        if command == 'short:att':
            if self.running:
                t = self.mode_time()
                s = self.speed
                angle = self.params['calib_angle']
                return str(t * s / angle)
            else:
                return "program not running"

    def start(self):
        ModeProgram.start(self)
        self.running = True

    def stop(self):
        ModeProgram.stop(self)
        self.running = False

    def move(self):
        myro.rotate(self.speed)
