# Copyright 2014 Mitchell Kember and Charles Bai. Subject to the MIT License.

"""Makes the Scribbler Bot trace shapes with a marker."""

import json
import math
from time import time

from scribbler.util import deg_to_rad, rad_to_deg, dist_2d, equiv_angle
from scribbler.programs.base import ModeProgram


# Short codes for the parameters of the program.
PARAM_CODES = {
    'rs': 'rotation_speed',
    'ps': 'point_scale',
    'mr': 'min_rotation'
}

# Default values for the parameters of the program.
PARAM_DEFAULTS = {
    'speed': 0.1,
    'angle_to_time': 0.0052,
    'rotation_speed': 0.1, # 0.4, # from 0.0 to 1.0
    'point_scale': 0.02, #0.05, # cm/px
    'min_rotation': 2 # deg
}

POINTS_PREFIX = 'points:'


class Tracie(ModeProgram):

    """Tracie takes a set of points as input and draws the shape with a pen."""

    def __init__(self):
        # self.new_points is the list of points that will be used next.
        # It persists across resets.
        self.new_points = []
        ModeProgram.__init__(self, 0)
        self.add_params(PARAM_DEFAULTS, PARAM_CODES)

    def reset(self):
        ModeProgram.reset(self)
        self.points = None # path the the robot draws
        self.index = 0 # index of point robot is going towards
        self.heading = math.pi / 2 # the current heading, in standard position
        self.rot_dir = 1 # 1 for counterclockwise, -1 for clockwise
        self.go_for = 0 # the time duration of the robot's current action
        # These two are only needed because the status method needs to access
        # them after they have been set by the time setting methods.
        self.delta_angle = 0
        self.delta_pos = 0

    def __call__(self, command):
        p_status = ModeProgram.__call__(self, command)
        if p_status:
            return p_status
        if command.startswith(POINTS_PREFIX):
            json_str = command[len(POINTS_PREFIX):]
            self.new_points = self.transform_points(json.loads(json_str))
            return "received {} points".format(str(len(self.new_points)))
        if command == 'short:trace':
            if self.mode == 0:
                return "0 {}".format(self.heading)
            if self.mode == 'halt':
                return "{} {}".format(len(self.points)-1, self.heading)
            t = self.mode_time()
            T = self.go_for
            i = self.index - 1
            delta_i = 1
            theta = self.heading
            delta_theta = 0
            if self.mode == 'rotate':
                delta_i = 0
                delta_theta = self.delta_angle
                theta -= delta_theta
            vals = [t, T, i, delta_i, theta, delta_theta]
            return ' '.join(map(str, vals));

    def transform_points(self, data):
        """Parses the point data and translates all points to make the firs
        point the origin. Returns the resulting points list."""
        x0 = float(data[0]['x'])
        y0 = float(data[0]['y'])
        return [(float(p['x']) - x0, float(p['y']) - y0) for p in data]

    @property
    def speed(self):
        # This looks wrong, but the speed is actually used just before the mode
        # switch, so it needs to be this way.
        if self.mode == 'drive':
            return self.params['rotation_speed']
        return self.params['speed']

    def is_mode_done(self):
        """Returns true if the current mode is finished, and false otherwise.
        The 'halt' mode is never done."""
        z = self.mode == 0
        halt = self.mode == 'halt'
        return z or (not halt and self.has_elapsed(self.go_for))

    def next_mode(self):
        """Switches to the next mode and starts it."""
        if self.mode == 'halt':
            return
        if self.mode == 0:
            # Use the points that were sent most recently.
            self.points = self.new_points[:]
        if self.mode == 'rotate':
            self.set_drive_time()
            self.goto_mode('drive')
        elif self.mode == 0 or self.mode == 'drive':
            self.index += 1
            if self.index < len(self.points):
                self.set_rotate_time()
                # Don't even try to rotate if it's a very small angle, because
                # the robot will go too far; it is better to go straight.
                min_rad = deg_to_rad(self.params['min_rotation'])
                if abs(self.delta_angle) < min_rad:
                    self.set_drive_time()
                    self.goto_mode('drive')
                else:
                    self.goto_mode('rotate')
            else:
                self.goto_mode('halt')

    def set_drive_time(self):
        """Sets the time duration for which the robot should drive in order to
        get to the next point."""
        x1, y1 = self.points[self.index -1]
        x2, y2 = self.points[self.index]
        # Scale by the point_sacle now, rather than in the transform method,
        # because the user can change this value at any time.
        distance = self.params['point_scale'] * dist_2d(x1, y1, x2, y2)
        self.go_for = self.dist_to_time(distance)
        self.delta_pos = distance

    def set_rotate_time(self):
        """Sets the time duration for which the robot should rotate in order to
        be facing the next point."""
        new_heading = self.next_point_angle()
        delta = equiv_angle(new_heading - self.heading)
        self.rot_dir = 1 if delta > 0 else -1
        self.go_for = self.angle_to_time(rad_to_deg(self.rot_dir * delta))
        self.heading = new_heading
        self.delta_angle = delta

    def next_point_angle(self):
        """Calculates the angle that the line connecting the current point and
        the next point makes in standard position."""
        x1, y1 = self.points[self.index-1]
        x2, y2 = self.points[self.index]
        return math.atan2(y2 - y1, x2 - x1)

    def move(self):
        """Makes Myro calls to move the robot according to the current mode.
        Called when the mode is begun and whenever the program is resumed."""
        ModeProgram.move(self)
        if self.mode == 0 or self.mode == 'halt':
            myro.stop()
        if self.mode == 'drive':
            myro.forward(self.speed)
        if self.mode == 'rotate':
            myro.rotate(self.rot_dir * self.speed)

    def status(self):
        """Return the status message that should be displayed at the beginning
        of the current mode."""
        if self.mode == 0:
            return "impossible"
        if self.mode == 'halt':
            return "finished drawing"
        if self.mode == 'drive':
            return "drive {:.2f} cm".format(self.delta_pos)
        if self.mode == 'rotate':
            return "rotate {:.2f} degrees".format(rad_to_deg(self.delta_angle))

    def no_start(self):
        if len(self.new_points) <= 1:
            return "not enough points"
        return False

    def loop(self):
        ModeProgram.loop(self)
        if self.is_mode_done():
            self.next_mode()
            return self.status()
