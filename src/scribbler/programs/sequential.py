# Copyright 2014 Mitchell Kember. Subject to the MIT License.

"""Implements an early program-type that we are no longer using."""

import time.time

from scribbler.util import average
from scribbler.programs.base import BaseProgram, obstacle_average


class SeqProgram(BaseProgram):

    """A program that interprets a sequence of instructions.

    The sequence is a list of modes. A mode is represented by a triple of the
    form `(i, c, p, s)` where `i` is an instruction string, `c` is the
    condition, `p` is the parameter of the condition, and `s` is the status
    message to display. The program beings by performing the instruction of the
    first mode, and it moves on to the next mode when the condition of the first
    mode is met. After the last mode, we return to the first mode.
    """

    def __init__(self, seq):
        """Creates a program that interprets the given sequence."""
        BaseProgram.__init__(self)
        self.seq = seq
        self.build_maps()
        self.reset()

    def build_maps(self):
        self.instructions = {
            'fwd': lambda t: myro.forward(self.speed),
            'bwd': lambda t: myro.backward(self.speed),
            'ccw': lambda t: myro.rotate(self.speed),
            'cw': lambda t: myro.rotate(-self.speed)
        }
        self.conditions = {
            'ir>': lambda v: average(myro.getObstacle()) > v,
            'time': lambda t: self.time > t,
            'dist': lambda d: self.time > dist_to_time(d, self.speed),
            'angle': lambda a: self.time > angle_to_time(a, self.speed),
            'forever': lambda _: False,
        }

    @property
    def time(self):
        """Returns the time elapsed since the current mode was started."""
        return time.time() - self.start_time

    def increment_mode(self):
        """Increments the mode index (wrapping around if necessary), updates
        mode variables, and resets the timer."""
        myro.stop()
        self.mode_ind += 1
        self.mode_ind %= len(self.seq)
        self.i, self.c, self.p, self.s = self.seq[self.mode_ind]
        self.start_time = time.time()

    def reset(self):
        """Resets the program to the first mode."""
        BaseProgram.reset(self)
        self.mode_ind = -1

    def stop(self):
        """Record the time when the program is paused."""
        BaseProgram.stop(self)
        self.pause_time = time.time()

    def start(self):
        """Fixes the start time so that the pause doesn't count towards the
        elapsed time, and continues the previous motion of the robot."""
        BaseProgram.start(self)
        self.start_time += time.time() - self.pause_time
        self.perform_instruction()

    def perform_instruction(self):
        """Performs the instruction dictated by the current mode."""
        self.instructions[self.i](self.p)

    def condition_satisfied(self):
        """Returns whether the current mode's condition is satisfied."""
        return self.mode_ind == -1 or self.conditions[self.c](self.p)

    def loop(self):
        """Advances to the next mode and performs the instruction when it is
        time (when the condition is met), otherwise does nothing."""
        BaseProgram.loop(self)
        if self.condition_satisfied():
            self.increment_mode()
            self.perform_instruction()
            return self.s

    def __call__(self, command):
        base_response = BaseProgram.__call__(self, command)
        if base_response:
            return base_response
        return "unrecognized command"
