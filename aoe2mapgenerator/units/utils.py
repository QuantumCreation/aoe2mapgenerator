"""
Holds various utility functions for placing objects on a map.
"""

import random


def default_clumping_func(p1, p2, clumping):
    """
    Default clumping function.

    Args:
        p1: First point.
        p2: Second point.
        clumping: Factor to determine how clumped placed objects in a group are.
    """
    if clumping == -1:
        clumping = 999

    distance = (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
    return (distance) + random.random() * (clumping) ** 2
