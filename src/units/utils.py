"""
Holds various utility functions for placing objects on a map.
"""

import random
from typing import List
import numpy as np


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


def manhattan_distance(p1: tuple, p2: tuple) -> int:
    """
    Calculates the Manhattan distance between two points.

    Args:
        p1: First point.
        p2: Second point.
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def connect_points_with_randomization(
    key_point_list: List[tuple[int, int]],
    splits: int,
    random_shift_range: int,
    base_points: List[tuple[int, int]] = None,
) -> List[tuple[int, int]]:
    """
    Creates list of all connecting points with additional randomization for a list of points.

    Args:
        key_point_list: List of points in order that will be connected, these points will always be included in the final list.
        point_list: List of points in order
        splits: Number of splits to add
        random_shift_range: Range to shift each point along the original main line
    """
    if not base_points:
        base_points = connect_points(key_point_list)
    else:
        if not _check_base_point_valid(base_points, key_point_list):
            raise ValueError("Base points must include all key points.")

    new_point_indicies = get_indicies_of_key_points(base_points, key_point_list)

    for i in range(splits + 2):
        index = int(((len(base_points) - 1) / (splits + 1)) * (i))
        new_point_indicies.append(index)

    new_point_indicies.sort()
    new_points = [base_points[i] for i in new_point_indicies]

    for i, point in enumerate(new_points):
        if point not in key_point_list:
            new_points[i] = (
                point[0] + random.randint(-random_shift_range, random_shift_range),
                point[1] + random.randint(-random_shift_range, random_shift_range),
            )

    randomized_points = connect_points(new_points)
    return randomized_points


def connect_points(point_list: List[tuple[int, int]]) -> List[tuple[int, int]]:
    """
    Creates list of all connecting points for a list of outer perimeter points.

    Args:
        point_list: list of outer perimeter points in order

    Returns list of points connecting each adjacent set of perimeter points
    """
    returned_points = []

    for i, (x, y) in enumerate(point_list[:-1]):
        next_point = [
            point_list[(i + 1) % len(point_list)][0],
            point_list[(i + 1) % len(point_list)][1],
        ]
        new_points = _connect(np.array([[x, y], next_point]))
        returned_points.extend(new_points)

    return [tuple(point) for point in np.array(returned_points)]


def _check_base_point_valid(
    base_points: List[tuple[int, int]], key_points: List[tuple[int, int]]
) -> bool:
    """
    Checks if the base points are valid.

    Args:
        base_points: List of base points.
    """
    for key_point in key_points:
        if key_point not in base_points:
            return False
    return True


def get_indicies_of_key_points(
    base_points: List[tuple[int, int]], key_points: List[tuple[int, int]]
) -> List[int]:
    """
    Gets the indicies of the key points in the base points list.

    Args:
        base_points: List of base points.
        key_points: List of key points.
    """
    key_point_indicies = []
    for key_point in key_points:
        key_point_indicies.append(base_points.index(key_point))

    return list(reversed(key_point_indicies))


def _connect(ends: np.ndarray[np.int32]) -> np.ndarray[np.int32]:
    """
    Connects a start and end point.

    Args:
        ends: List with a start (x,y) coordinate and an end (x,y) coordinate.
    """
    d0, d1 = np.abs(np.diff(ends, axis=0))[0]
    if d0 > d1:
        return np.c_[
            np.linspace(ends[0, 0], ends[1, 0], d0 + 1, dtype=np.int32),
            np.round(np.linspace(ends[0, 1], ends[1, 1], d0 + 1)).astype(np.int32),
        ]
    return np.c_[
        np.round(np.linspace(ends[0, 0], ends[1, 0], d1 + 1)).astype(np.int32),
        np.linspace(ends[0, 1], ends[1, 1], d1 + 1, dtype=np.int32),
    ]
