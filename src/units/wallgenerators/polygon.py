"""
Generates a polygonal wall.
"""

import numpy as np
from matplotlib.pylab import matshow
import matplotlib.pyplot as plt
from typing import List
from aoe2mapgenerator.src.units.utils import connect_points


def generate_polygonal_wall(
    x: int, y: int, number_of_sides: int, radius: int
) -> List[tuple[int, int]]:
    """
    Generatres a polygonal wall centered around the x and y coordinates.

    Args:
        x: x coordinate center.
        y: y coordinate center.
        corner_points: Number of corners for polygon.
        radius: Radius of the polygon.
    """
    points = generate_polygonal_wall_points(x, y, number_of_sides, radius)
    points = points + [points[0]]
    points = connect_points(points)

    return points


def generate_polygonal_wall_points(x: int, y: int, number_of_sides: int, radius: int):
    """
    Generates sequential points forming the outer perimeter of a wall.

    Args:
        x: x coordinate to center the wall.
        y: y coordinate to center the wall.
        corner_points: Number of corner pointers to create.
        radius: radius of the walls.

    Returns points to define the outer perimeter.
    """
    points = []
    angles = np.array(list(range(number_of_sides))) * (2 * np.pi) / number_of_sides

    # Rotate all angles so that the shape aligns nicely on the grid for most cases
    rotated_angles = angles + (np.pi / number_of_sides)

    for i, rotated_angle in enumerate(rotated_angles):
        px = np.cos(rotated_angle) * radius
        py = np.sin(rotated_angle) * radius
        px = int(px)
        py = int(py)
        points.append([x + px, y + py])

    return points


def valid(array: List[List[tuple[int, int]]], x: int, y: int):
    """
    Checks that point coordinates are valid
    """
    return (0 <= x < len(array)) and (0 <= y < len(array[0]))
