# Copyright 2014 Mitchell Kember. Subject to the MIT License.

"""Makes the Scribbler Bot drive around an obstacle."""

from scribbler.util import average
from scribbler.programs.base import ModeProgram


# Short codes for the parameters of the program.
PARAM_CODES = {
    'sd': 'obstacle_slowdown',
    'ot': 'obstacle_thresh',
    'cr': 'compare_rotation',
    'nn': 'not_ninety',
    'cd': 'check_dist',
    'of': 'overshoot_front',
    'os': 'overshoot_side',
    'bi': 'bias',
    'rf': 'return_factor'
}

# Default values for the parameters of the program.
PARAM_DEFAULTS = {
    'obstacle_slowdown': 0.2,
    'obstacle_thresh': 1, # from 0 to 6400
    'compare_rotation': 25, # deg
    'not_ninety': 80, # deg
    'check_dist': 8.0, # cm
    'overshoot_front': 10.0, # cm
    'overshoot_side': 14.0, # cm
    'bias': 0, # from -1 to 1
    'return_factor': 0.75
}

# Statuses to be displayed at the beginning of each mode.
STATUSES = {
    'fwd-1': "driving forward",
    'ccw-c': "checking slant",
    'cw-c': "unchecking slant",
    'ccw-1': "turning 90 ccw",
    'fwd-2': "driving along",
    'cw-1': "checking obstacle",
    'ccw-2': "unturning",
    'fwd-3': "going further",
    'cw-2': "returning",
    'fwd-4': "past front edge",
    'fwd-5': "past back edge",
    'ccw-3': "straightening up"
}


class Avoider(ModeProgram):

    """The fourth generation of the object avoidance program."""

    def __init__(self):
        ModeProgram.__init__(self, 0)
        self.add_params(PARAM_DEFAULTS, PARAM_CODES)

    def reset(self):
        ModeProgram.reset(self)
        self.x_pos = 0
        self.heading = 'up'
        self.around_mult_f = 1
        self.around_mult = 1
        self.first_obstacle_reading = 0
        self.side = 'front'

    @property
    def speed(self):
        if self.mode in ['fwd-1', 'ccw-c', 'cw-c', 'fwd-4', 'fwd-5']:
            return self.params['obstacle_slowdown']
        return self.params['speed']

    def status(self):
        """Return the status message that should be displayed at the beginning
        of the current mode."""
        return STATUSES.get(self.mode, "bad mode" + str(self.mode))

    def goto(self, mode):
        """Switches to the given mode and returns its status."""
        self.goto_mode(mode)
        return self.status()

    def mode_direction(self):
        """Returns the identifier of the direction of motion for this mode."""
        if self.mode == 0:
            return None
        return self.mode.split('-')[0]

    def has_rotated(self, angle):
        """Returns true if the robot has rotated by `angle` degrees during the
        current mode (assuming it is pivoting) and false otherwise. Takes the
        side of the box and the bias parameter into account."""
        d = self.mode_direction()
        m = self.around_mult
        t = self.angle_to_time(angle)
        if d == 'ccw':
            t *= 1 + m * self.params['bias']
        elif d == 'cw':
            t *= 1 - m * self.params['bias']
        return self.has_elapsed(t)

    def move(self):
        ModeProgram.move(self)
        direction = self.mode_direction()
        if direction == 'fwd':
            myro.forward(self.speed)
        if direction == 'bwd':
            myro.backward(self.speed)
        if direction == 'ccw':
            myro.rotate(self.around_mult * self.speed)
        if direction == 'cw':
            myro.rotate(self.around_mult * -self.speed)

    def loop(self):
        ModeProgram.loop(self)
        if self.mode == 0:
            return self.goto('fwd-1')
        if self.mode == 'fwd-1':
            d = obstacle_average()
            if d > self.params['obstacle_thresh']:
                self.first_obstacle_reading = d
                return self.goto('ccw-c')
        if self.mode == 'ccw-c':
            if self.has_rotated(self.params['compare_rotation']):
                myro.stop()
                d = obstacle_average()
                if d < self.first_obstacle_reading:
                    self.around_mult_f = 1
                else:
                    self.around_mult_f = -1
                return self.goto('cw-c')
        if self.mode == 'cw-c':
            if self.has_rotated(self.params['compare_rotation']):
                self.around_mult = self.around_mult_f
                return self.goto('ccw-1')
        if self.mode == 'ccw-1':
            if self.at_right_angle():
                return self.goto('fwd-2')
        if self.mode == 'fwd-2':
            if self.has_travelled(self.params['check_dist']):
                return self.goto('cw-1')
        if self.mode == 'cw-1':
            if self.at_right_angle():
                myro.stop()
                if obstacle_average() > self.params['obstacle_thresh']:
                    return self.goto('ccw-1')
                else:
                    return self.goto('ccw-2')
        if self.mode == 'ccw-2':
            if self.at_right_angle():
                return self.goto('fwd-3')
        if self.mode == 'fwd-3':
            if self.has_travelled(self.params['overshoot_front']):
                return self.goto('cw-2')
        if self.mode == 'cw-2':
            if self.at_right_angle():
                if self.side == 'front':
                    return self.goto('fwd-4')
                else:
                    return self.goto('fwd-5')
        if self.mode == 'fwd-4':
            if self.has_travelled(self.params['overshoot_side']):
                self.side = 'side'
                return self.goto('cw-1')
            if obstacle_average() > self.params['obstacle_thresh']:
                myro.stop()
                return self.goto('ccw-1')
        if self.mode == 'fwd-5':
            if self.has_travelled(self.x_pos * self.params['return_factor']):
                return self.goto('ccw-3')
            if obstacle_average() > self.params['obstacle_thresh']:
                myro.stop()
                return self.goto('ccw-1')
        if self.mode == 'ccw-3':
            if self.at_right_angle():
                self.reset()
                self.start()
                return "restarting program"

    def end_mode(self):
        ModeProgram.end_mode(self)
        if self.mode in ['fwd-1', 'ccw-c', 'cw-c']:
            return
        # Keep track of the current x-position.
        d = self.mode_direction()
        dist = self.time_to_dist(self.mode_time())
        if d == 'fwd':
            if self.heading == 'out':
                self.x_pos += dist
            elif self.heading == 'in':
                self.x_pos -= dist 
        elif d == 'bwd':
            if self.heading == 'out':
                self.x_pos -= dist
            elif self.heading == 'in':
                self.x_pos += dist
        elif d == 'ccw':
            if self.heading == 'up':
                self.heading = 'out'
            elif self.heading == 'in':
                self.heading = 'up'
        elif d == 'cw':
            if self.heading == 'up':
                self.heading = 'in'
            elif self.heading == 'out':
                self.heading = 'up'


def obstacle_average():
    """Returns the average of the three obstacle sensor readings."""
    return average(myro.getObstacle())
