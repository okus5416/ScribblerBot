# Copyright 2014 Mitchell Kember. Subject to the MIT License.

"""Some common mathematical utility functions."""

import math


def average(xs):
    """Returns the floating-point average of a list of numbers."""
    return sum(xs) / float(len(xs))


def rad_to_deg(theta):
    """Converts radians to degrees."""
    return 180.0 * theta / math.pi


def deg_to_rad(theta):
    """Converts degrees to radians."""
    return math.pi * theta / 180


def dist_2d(x1, y1, x2, y2):
    """Returns the distance between (x1,y1) and (x2,y2)."""
    return math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))


def equiv_angle(theta):
    """Returns the smallest angle (positive or negative) that is equivalent to
    `theta`. For example, 3/2*PI will be converted to -1/2*PI."""
    while theta > math.pi:
        theta -= 2 * math.pi
    while theta < -math.pi:
        theta += 2 * math.pi
    return theta
