"""
Generates a polygonal wall.
"""

import numpy as np
from matplotlib.pylab import matshow
import matplotlib.pyplot as plt
from typing import List, Tuple
from src.units.utils import connect_points


def generate_polygonal_wall_points(
    point: Tuple[int, int], number_of_sides: int, radius: float
) -> List[Tuple[int, int]]:
    """
    Generates a polygonal wall centered around the x and y coordinates.

    Args:
        x: x coordinate center.
        y: y coordinate center.
        number_of_sides: Number of corners for polygon.
        radius: Radius of the polygon.
    """
    points = generate_polygonal_wall_corner_points(point, number_of_sides, radius)
    points = points + [points[0]]
    points = connect_points(points)

    return points


def generate_polygonal_wall_corner_points(
    point: Tuple[int, int], number_of_sides: int, radius: float
) -> List[Tuple[int, int]]:
    """
    Generates only the corner points along the perimeter of the polygon.

    Args:
        x: x coordinate to center the wall.
        y: y coordinate to center the wall.
        number_of_sides: Number of corner points to create.
        radius: radius of the walls.

    Returns points to define the outer perimeter.
    """
    x, y = point
    points: List[Tuple[int, int]] = []
    angles = np.array(list(range(number_of_sides))) * (2 * np.pi) / number_of_sides

    # Rotate all angles so that the shape aligns nicely on the grid for most cases
    rotated_angles = angles + (np.pi / number_of_sides)

    for i, rotated_angle in enumerate(rotated_angles):
        px = np.cos(rotated_angle) * radius
        py = np.sin(rotated_angle) * radius
        px = int(px)
        py = int(py)
        points.append((x + px, y + py))

    return points


def valid(array: List[List[Tuple[int, int]]], x: int, y: int) -> bool:
    """
    Checks that point coordinates are valid
    """
    return (0 <= x < len(array)) and (0 <= y < len(array[0]))
