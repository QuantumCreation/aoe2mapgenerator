"""
Generates a polygonal wall.
"""

import numpy as np
from matplotlib.pylab import matshow
import matplotlib.pyplot as plt
from typing import List, Tuple
from aoe2mapgenerator.units.utils import connect_points


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


def generate_star_fort_wall_points(
    center: Tuple[int, int],
    gate_half_span: int,
    curtain_reach: int,
) -> List[Tuple[int, int]]:
    """Generate a Vauban-style bastioned star fort perimeter.

    The shape is an 8-cornered polygon whose wall segments are *only*
    horizontal, vertical, or 45 ° diagonal — satisfying AoE2's grid-aligned
    wall constraint.

    Layout (clockwise from the top-left corner of the North gate wall)::

                   ___           ← North gate wall  (horizontal)
                  /   \\          ← NE curtain wall   (45 °)
                 |     |         ← East gate wall    (vertical)
                  \\   /          ← SE curtain wall   (45 °)
                   ‾‾‾           ← South gate wall   (horizontal)

    Bastions project at all four cardinal points.  The corners where flat
    gate walls meet diagonal curtain walls are ideal spots for flanking
    towers.

    Args:
        center: (x, y) centre tile of the fort.
        gate_half_span: Half the width of each flat gate wall (``B`` in docs).
            A reasonable default is ``3–6``.
        curtain_reach: Length of each 45 ° curtain wall (``R`` in docs); also
            the half-side-length of the implied inner square.  The effective
            "inscribed radius" of the fort is ``curtain_reach + gate_half_span``.

    Returns:
        Ordered list of all wall tile positions (duplicates removed).
    """
    cx, cy = center
    B = gate_half_span
    R = curtain_reach

    # 8 corners in clockwise order.
    # Segment directions: N gate (horizontal), NE curtain (45°),
    # E gate (vertical), SE curtain (135°), S gate (horizontal),
    # SW curtain (225°), W gate (vertical), NW curtain (315°).
    corners: List[Tuple[int, int]] = [
        (cx - B, cy - R - B),  # W end of North gate wall
        (cx + B, cy - R - B),  # E end of North gate wall
        (cx + R + B, cy - B),  # N end of East gate wall
        (cx + R + B, cy + B),  # S end of East gate wall
        (cx + B, cy + R + B),  # E end of South gate wall
        (cx - B, cy + R + B),  # W end of South gate wall
        (cx - R - B, cy + B),  # S end of West gate wall
        (cx - R - B, cy - B),  # N end of West gate wall
    ]

    closed: List[Tuple[int, int]] = corners + [corners[0]]
    return connect_points(closed)


def get_star_fort_corner_points(
    center: Tuple[int, int],
    gate_half_span: int,
    curtain_reach: int,
) -> List[Tuple[int, int]]:
    """Return the 8 corner points of a star fort (no interpolation).

    These are the elbow positions where each flat gate wall meets a diagonal
    curtain wall — ideal spots for flanking guard towers.

    Args:
        center: (x, y) centre tile.
        gate_half_span: Same ``B`` parameter as :func:`generate_star_fort_wall_points`.
        curtain_reach: Same ``R`` parameter as :func:`generate_star_fort_wall_points`.

    Returns:
        8 corner ``(x, y)`` tuples in clockwise order.
    """
    cx, cy = center
    B = gate_half_span
    R = curtain_reach
    return [
        (cx - B, cy - R - B),
        (cx + B, cy - R - B),
        (cx + R + B, cy - B),
        (cx + R + B, cy + B),
        (cx + B, cy + R + B),
        (cx - B, cy + R + B),
        (cx - R - B, cy + B),
        (cx - R - B, cy - B),
    ]


def get_star_fort_cardinal_gate_midpoints(
    center: Tuple[int, int],
    gate_half_span: int,
    curtain_reach: int,
) -> List[Tuple[int, int]]:
    """Return the midpoint of each of the 4 cardinal gate walls.

    These are the most natural positions for a fort gate and are also used
    as path start-points when drawing roads from gates to the central castle.

    Args:
        center: (x, y) centre tile.
        gate_half_span: Same ``B`` parameter as :func:`generate_star_fort_wall_points`.
        curtain_reach: Same ``R`` parameter as :func:`generate_star_fort_wall_points`.

    Returns:
        4 ``(x, y)`` midpoints in [North, East, South, West] order.
    """
    cx, cy = center
    B = gate_half_span
    R = curtain_reach
    _ = B  # gate_half_span is not needed for the midpoint (it cancels out)
    return [
        (cx, cy - R - B),   # North gate midpoint
        (cx + R + B, cy),   # East gate midpoint
        (cx, cy + R + B),   # South gate midpoint
        (cx - R - B, cy),   # West gate midpoint
    ]
