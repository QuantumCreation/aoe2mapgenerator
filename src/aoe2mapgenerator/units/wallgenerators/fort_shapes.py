"""Fort shape generators for FortTemplate.

All generators return a :class:`FortShape` whose wall segments are restricted
to the 8 canonical AoE2 grid directions (multiples of 45 °):

    0 °  — East / rightward (horizontal)
    45 ° — South-East diagonal
    90 ° — South / downward (vertical)
    135 °— South-West diagonal
    (and their mirror counterparts at 180 °, 225 °, 270 °, 315 °)

Available shape generators
---------------------------
``square``      — axis-aligned square.
``rectangle``   — axis-aligned rectangle with independent width / height.
``octagon``     — regular screen-octagon (4 flat sides + 4 chamfered corners).
``star``        — Vauban bastioned star fort (4 cardinal bastions with
                  4 × diagonal curtain walls).  This is the shape from the
                  earlier implementation.
``voronoi``     — take the central cell of a Voronoi diagram, then snap all
                  its edges onto the 45 ° grid to make it AoE2-valid.
``grammar``     — start from a rectangle then iteratively apply three
                  production rules — BUMP (rectangular extrusion), NOTCH
                  (rectangular indentation), and CHAMFER (45 ° corner cut) —
                  to produce an interesting, varied fort outline.

Usage::

    shape = build_fort_shape("grammar", center=(100, 100), base_width=24,
                             base_height=20, iterations=6, seed=42)
    # shape.wall_points   → place wall tiles
    # shape.corner_points → place guard towers
    # shape.gate_points   → approximate gate positions (paths / decorations)
    # shape.inscribed_radius → interior radius for troop placement
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
from scipy.spatial import Voronoi

from aoe2mapgenerator.units.utils import connect_points
from aoe2mapgenerator.units.wallgenerators.polygon import (
    generate_star_fort_wall_points,
    get_star_fort_cardinal_gate_midpoints,
    get_star_fort_corner_points,
)

# ---------------------------------------------------------------------------
# Public data type
# ---------------------------------------------------------------------------


@dataclass
class FortShape:
    """All geometry needed by FortTemplate to place walls, towers, and gates.

    Attributes:
        wall_points:      All rasterised wall-tile ``(x, y)`` positions.
        corner_points:    Positions for flanking guard towers.
        gate_points:      Approximate midpoints of each gate wall, used for
                          path drawing, gate-guard placement, and exterior
                          decorations.  (Actual gate *tiles* are placed by the
                          engine's ``gate_placer``, which finds the wall
                          boundary itself.)
        inscribed_radius: Approximate distance from the centre to the inner
                          face of the nearest wall — used to scale troop
                          placement rings.
        use_eight_side_gates: When ``True`` the template calls
                          ``place_gate_on_eight_sides``; when ``False`` (the
                          default) it calls ``place_gate_on_four_sides``.
    """

    wall_points: List[Tuple[int, int]]
    corner_points: List[Tuple[int, int]]
    gate_points: List[Tuple[int, int]]
    inscribed_radius: float
    use_eight_side_gates: bool = False


# ---------------------------------------------------------------------------
# Shared polygon utilities
# ---------------------------------------------------------------------------


def _rasterize_polygon(vertices: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Rasterise a closed polygon (list of integer vertices) to contiguous wall tiles.

    Connects every consecutive pair of vertices (including the closing edge
    back to the first vertex) using Bresenham-style line drawing.
    """
    if not vertices:
        return []
    closed = list(vertices) + [vertices[0]]
    pts = connect_points(closed)
    # Deduplicate while preserving order
    seen: set[Tuple[int, int]] = set()
    result: List[Tuple[int, int]] = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _cardinal_gate_points(
    wall_points: List[Tuple[int, int]],
    center: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """Return the 4 wall tiles that are most extreme in N / E / S / W directions.

    These serve as approximate gate positions for path drawing and decorations.
    They closely match where ``gate_placer.place_gate_on_four_sides`` will
    actually snap the gate tiles.
    """
    if not wall_points:
        return []
    cx, cy = center
    north = min(wall_points, key=lambda p: p[1])
    south = max(wall_points, key=lambda p: p[1])
    east  = max(wall_points, key=lambda p: p[0])
    west  = min(wall_points, key=lambda p: p[0])
    return [north, east, south, west]


def _eight_dir_gate_points(
    wall_points: List[Tuple[int, int]],
    center: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """Return 8 gate points in cardinal + inter-cardinal directions."""
    if not wall_points:
        return []
    cx, cy = center
    directions = [
        (0.0,  -1.0),  # N
        (1.0,  -1.0),  # NE
        (1.0,   0.0),  # E
        (1.0,   1.0),  # SE
        (0.0,   1.0),  # S
        (-1.0,  1.0),  # SW
        (-1.0,  0.0),  # W
        (-1.0, -1.0),  # NW
    ]
    gates: List[Tuple[int, int]] = []
    for dx, dy in directions:
        best = max(  # most extreme point in this direction
            wall_points,
            key=lambda p: (p[0] - cx) * dx + (p[1] - cy) * dy,
        )
        gates.append(best)
    return gates


def _inscribed_radius_from_wall(
    wall_points: List[Tuple[int, int]],
    center: Tuple[int, int],
) -> float:
    """Minimum Euclidean distance from *center* to any wall tile."""
    if not wall_points:
        return 1.0
    cx, cy = center
    return min(math.hypot(p[0] - cx, p[1] - cy) for p in wall_points)


# ---------------------------------------------------------------------------
# Shape generators
# ---------------------------------------------------------------------------


def make_square(
    center: Tuple[int, int],
    half_size: int = 16,
) -> FortShape:
    """Axis-aligned square fort.

    Args:
        center:    (x, y) centre tile.
        half_size: Distance from the centre to each wall face.  The outer
                   bounding box is ``(2*half_size + 1)² tiles``.  Default 16.
    """
    cx, cy = center
    H = half_size
    vertices = [
        (cx - H, cy - H),
        (cx + H, cy - H),
        (cx + H, cy + H),
        (cx - H, cy + H),
    ]
    wall_pts = _rasterize_polygon(vertices)
    return FortShape(
        wall_points=wall_pts,
        corner_points=list(vertices),
        gate_points=_cardinal_gate_points(wall_pts, center),
        inscribed_radius=float(H),
        use_eight_side_gates=False,
    )


def make_rectangle(
    center: Tuple[int, int],
    width: int = 30,
    height: int = 20,
) -> FortShape:
    """Axis-aligned rectangular fort.

    Args:
        center: (x, y) centre tile.
        width:  Total width of the fort in tiles (E-W extent).  Default 30.
        height: Total height of the fort in tiles (N-S extent).  Default 20.
    """
    cx, cy = center
    hw, hh = width // 2, height // 2
    vertices = [
        (cx - hw, cy - hh),
        (cx + hw, cy - hh),
        (cx + hw, cy + hh),
        (cx - hw, cy + hh),
    ]
    wall_pts = _rasterize_polygon(vertices)
    return FortShape(
        wall_points=wall_pts,
        corner_points=list(vertices),
        gate_points=_cardinal_gate_points(wall_pts, center),
        inscribed_radius=float(min(hw, hh)),
        use_eight_side_gates=False,
    )


def make_octagon(
    center: Tuple[int, int],
    radius: int = 16,
) -> FortShape:
    """Regular screen-octagon fort.

    The octagon has 4 axis-aligned faces (N/E/S/W) and 4 diagonal (45 °)
    corner segments, all of which are AoE2-valid.  The chamfer size is set to
    ``radius // 3`` to produce a visually pleasing shape.

    Args:
        center: (x, y) centre tile.
        radius: Approximate half-side length (distance from centre to the
                midpoint of an axis-aligned face).  Default 16.
    """
    cx, cy = center
    R = radius
    c = max(2, R // 3)   # chamfer = length of each 45 ° corner cut
    f = R - c             # distance from centre to where the diagonal starts

    # Clockwise in y-down screen space (AoE2 coords):
    vertices: List[Tuple[int, int]] = [
        (cx - f, cy - R),   # NW start of N face
        (cx + f, cy - R),   # NE end   of N face
        (cx + R, cy - f),   # NE start of E face  (after NE chamfer)
        (cx + R, cy + f),   # SE end   of E face
        (cx + f, cy + R),   # SE start of S face  (after SE chamfer)
        (cx - f, cy + R),   # SW end   of S face
        (cx - R, cy + f),   # SW start of W face  (after SW chamfer)
        (cx - R, cy - f),   # NW end   of W face
    ]
    wall_pts = _rasterize_polygon(vertices)
    return FortShape(
        wall_points=wall_pts,
        corner_points=list(vertices),   # 8 elbow corners for towers
        gate_points=_eight_dir_gate_points(wall_pts, center),
        inscribed_radius=float(R),
        use_eight_side_gates=True,
    )


def make_star(
    center: Tuple[int, int],
    gate_half_span: int = 4,
    curtain_reach: int = 14,
) -> FortShape:
    """Vauban bastioned star fort (original implementation).

    4 flat cardinal bastions connected by 4 diagonal 45 ° curtain walls.

    Args:
        center:          (x, y) centre tile.
        gate_half_span:  Half-width of each flat gate wall.  Default 4.
        curtain_reach:   Length of each 45 ° curtain wall segment.  Default 14.
    """
    wall_pts  = generate_star_fort_wall_points(center, gate_half_span, curtain_reach)
    corners   = get_star_fort_corner_points(center, gate_half_span, curtain_reach)
    gate_pts  = get_star_fort_cardinal_gate_midpoints(center, gate_half_span, curtain_reach)
    radius    = float(curtain_reach + gate_half_span)
    return FortShape(
        wall_points=wall_pts,
        corner_points=corners,
        gate_points=gate_pts,
        inscribed_radius=radius,
        use_eight_side_gates=False,
    )


def make_voronoi_fort(
    center: Tuple[int, int],
    radius: int = 18,
    num_sites: int = 14,
    seed: int | None = None,
) -> FortShape:
    """Fort whose outline is taken from the central cell of a Voronoi diagram.

    The raw Voronoi cell polygon (floating-point vertices) is clipped to a
    bounding box, all edges are **snapped to the nearest 45 ° grid angle**,
    and the result is rasterised into wall tiles.

    This produces an irregular, organic-looking fort shape that is still
    fully AoE2-valid because every wall segment is horizontal, vertical, or
    45 ° diagonal.

    Args:
        center:    (x, y) centre tile.
        radius:    Approximate outer radius of the fort.  Controls both the
                   region in which seed points are placed and the clipping
                   box size.  Default 18.
        num_sites: Number of random Voronoi seed points.  More sites → smaller,
                   more irregular cells.  Default 14.
        seed:      Optional random seed for reproducibility.
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    cx, cy = center

    # --- generate seed points -------------------------------------------
    # Scatter `num_sites` points in an annulus between radius*0.4 and radius*1.6
    # to ensure the central cell isn't too small or too large.
    angles = np_rng.uniform(0, 2 * math.pi, num_sites)
    radii  = np_rng.uniform(radius * 0.4, radius * 1.6, num_sites)
    sites  = np.column_stack([cx + radii * np.cos(angles),
                               cy + radii * np.sin(angles)])

    # Add 4 far sentinels to bound all Voronoi regions (avoid infinite ridges).
    far = radius * 6
    sentinels = np.array([
        [cx - far, cy - far],
        [cx + far, cy - far],
        [cx + far, cy + far],
        [cx - far, cy + far],
    ], dtype=float)
    all_points = np.vstack([sites, sentinels])

    vor = Voronoi(all_points)

    # --- find the cell whose site is closest to center -------------------
    dists = np.hypot(sites[:, 0] - cx, sites[:, 1] - cy)
    best_site_idx = int(np.argmin(dists))

    region_idx = vor.point_region[best_site_idx]
    region_vertex_indices = vor.regions[region_idx]

    if -1 in region_vertex_indices or len(region_vertex_indices) < 3:
        # Fallback: use the square shape if the Voronoi cell is ill-formed
        return make_square(center, half_size=radius)

    raw_vertices = vor.vertices[region_vertex_indices]  # shape (N, 2) float

    # --- clip to bounding box -------------------------------------------
    clip = radius * 1.1
    clipped: List[Tuple[float, float]] = []
    for vx, vy in raw_vertices:
        vx = max(cx - clip, min(cx + clip, vx))
        vy = max(cy - clip, min(cy + clip, vy))
        clipped.append((vx, vy))

    # --- round to integer and snap each edge to 45 ° -------------------
    int_verts = [(int(round(v[0])), int(round(v[1]))) for v in clipped]
    snapped  = _snap_polygon_edges_to_45(int_verts)

    wall_pts = _rasterize_polygon(snapped)
    if not wall_pts:
        return make_square(center, half_size=radius)

    corners  = snapped          # polygon vertices = tower positions
    gate_pts = _cardinal_gate_points(wall_pts, center)
    r        = _inscribed_radius_from_wall(wall_pts, center)

    return FortShape(
        wall_points=wall_pts,
        corner_points=corners,
        gate_points=gate_pts,
        inscribed_radius=r,
        use_eight_side_gates=False,
    )


def make_grammar_fort(
    center: Tuple[int, int],
    base_width: int = 26,
    base_height: int = 22,
    iterations: int = 6,
    seed: int | None = None,
) -> FortShape:
    """Grammar-based CSG fort shape.

    Starting from an axis-aligned rectangle the generator applies *iterations*
    random **production rules** drawn from:

    * **BUMP** — rectangular outward extrusion on an axis-aligned wall segment.
      Creates castellated battlements and projecting towers.
    * **NOTCH** — rectangular inward indentation (courtyard recesses,
      gate passages).
    * **CHAMFER** — replace a right-angle corner with a single 45 ° diagonal
      cut, softening the silhouette.

    Only BUMP and CHAMFER add outward extent; NOTCH and CHAMFER preserve or
    reduce the overall footprint.  All resulting edges are horizontal, vertical,
    or exactly 45 ° — AoE2-valid by construction.

    Args:
        center:      (x, y) centre tile.
        base_width:  Width of the starting rectangle in tiles.  Default 26.
        base_height: Height of the starting rectangle in tiles.  Default 22.
        iterations:  Number of grammar rule applications.  Higher values
                     produce more complex shapes.  Default 6.
        seed:        Optional random seed for reproducibility.
    """
    rng = random.Random(seed)
    cx, cy = center
    hw, hh = base_width // 2, base_height // 2

    # Initial polygon: clockwise in y-down coords
    poly: List[Tuple[int, int]] = [
        (cx - hw, cy - hh),  # TL
        (cx + hw, cy - hh),  # TR
        (cx + hw, cy + hh),  # BR
        (cx - hw, cy + hh),  # BL
    ]

    max_dim = max(base_width, base_height)
    min_bump_depth  = 2
    max_bump_depth  = max(3, max_dim // 8)
    min_bump_width  = 3
    chamfer_size    = max(2, max_dim // 10)
    max_notch_depth = max(2, max_dim // 10)

    for _ in range(iterations):
        # Gather eligible products
        bumps    = _find_eligible_bump_edges(poly, min_bump_width + 2)
        notches  = _find_eligible_notch_edges(poly, center, min_bump_width + 2, max_notch_depth)
        chamfers = _find_eligible_chamfer_corners(poly)

        candidates: List[Tuple[str, int]] = (
            [("bump", i) for i in bumps]   * 2 +
            [("notch", i) for i in notches] * 2 +
            [("chamfer", i) for i in chamfers] * 3
        )
        if not candidates:
            break

        rule, idx = rng.choice(candidates)

        if rule == "bump":
            depth = rng.randint(min_bump_depth, max_bump_depth)
            width = rng.randint(min_bump_width, max(min_bump_width, _edge_length(poly, idx) // 2))
            poly  = _apply_bump(poly, idx, depth, width, center)
        elif rule == "notch":
            depth = rng.randint(min_bump_depth, max(min_bump_depth, max_notch_depth))
            width = rng.randint(min_bump_width, max(min_bump_width, _edge_length(poly, idx) // 2))
            poly  = _apply_notch(poly, idx, depth, width, center)
        elif rule == "chamfer":
            poly  = _apply_chamfer(poly, idx, chamfer_size)

    wall_pts = _rasterize_polygon(poly)
    if not wall_pts:
        return make_square(center, half_size=max_dim // 2)

    corners  = list(poly)
    gate_pts = _cardinal_gate_points(wall_pts, center)
    r        = _inscribed_radius_from_wall(wall_pts, center)

    return FortShape(
        wall_points=wall_pts,
        corner_points=corners,
        gate_points=gate_pts,
        inscribed_radius=r,
        use_eight_side_gates=False,
    )


# ---------------------------------------------------------------------------
# Public dispatch
# ---------------------------------------------------------------------------

#: Registered shape names → human-readable description
SHAPE_REGISTRY: dict[str, str] = {
    "square":    "Axis-aligned square",
    "rectangle": "Axis-aligned rectangle",
    "octagon":   "Regular screen-octagon (8-sided)",
    "star":      "Vauban bastioned star fort",
    "voronoi":   "Organic Voronoi-cell fort (45 ° snapped)",
    "grammar":   "Grammar CSG fort (bump / notch / chamfer rules)",
}


def build_fort_shape(
    shape: str,
    center: Tuple[int, int],
    **kwargs,
) -> FortShape:
    """Dispatch to the appropriate fort shape generator.

    Args:
        shape:  One of ``"square"``, ``"rectangle"``, ``"octagon"``,
                ``"star"``, ``"voronoi"``, ``"grammar"``.
        center: (x, y) centre tile.
        **kwargs: Passed through to the matching generator.

    Shape-specific keyword arguments
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ``square``
        ``half_size`` (int, default 16)

    ``rectangle``
        ``width`` (int, default 30), ``height`` (int, default 20)

    ``octagon``
        ``radius`` (int, default 16)

    ``star``
        ``gate_half_span`` (int, default 4), ``curtain_reach`` (int, default 14)

    ``voronoi``
        ``radius`` (int, default 18), ``num_sites`` (int, default 14),
        ``seed`` (int | None, default None)

    ``grammar``
        ``base_width`` (int, default 26), ``base_height`` (int, default 22),
        ``iterations`` (int, default 6), ``seed`` (int | None, default None)

    Raises:
        ValueError: If *shape* is not a recognised name.
    """
    if shape == "square":
        return make_square(center,
                           half_size=kwargs.get("half_size", 16))
    if shape == "rectangle":
        return make_rectangle(center,
                              width=kwargs.get("width", 30),
                              height=kwargs.get("height", 20))
    if shape == "octagon":
        return make_octagon(center,
                            radius=kwargs.get("radius", 16))
    if shape == "star":
        return make_star(center,
                         gate_half_span=kwargs.get("gate_half_span", 4),
                         curtain_reach=kwargs.get("curtain_reach", 14))
    if shape == "voronoi":
        return make_voronoi_fort(center,
                                 radius=kwargs.get("radius", 18),
                                 num_sites=kwargs.get("num_sites", 14),
                                 seed=kwargs.get("seed", None))
    if shape == "grammar":
        return make_grammar_fort(center,
                                 base_width=kwargs.get("base_width", 26),
                                 base_height=kwargs.get("base_height", 22),
                                 iterations=kwargs.get("iterations", 6),
                                 seed=kwargs.get("seed", None))
    raise ValueError(
        f"Unknown fort shape {shape!r}. "
        f"Valid options: {list(SHAPE_REGISTRY)}"
    )


# ---------------------------------------------------------------------------
# Private: Voronoi edge snapping
# ---------------------------------------------------------------------------


def _snap_direction_to_45(dx: int, dy: int) -> Tuple[int, int]:
    """Return an integer vector pointing in the nearest of the 8 grid directions.

    The returned vector has Chebyshev-norm equal to 1 (i.e., each component
    is −1, 0, or +1), pointing in the same octant as *(dx, dy)*.
    """
    if dx == 0 and dy == 0:
        return (0, 0)
    # Snap angle to nearest multiple of 45°
    angle   = math.atan2(dy, dx)
    snapped = round(angle / (math.pi / 4)) * (math.pi / 4)
    sx = int(round(math.cos(snapped)))
    sy = int(round(math.sin(snapped)))
    return (sx, sy)


def _snap_polygon_edges_to_45(
    vertices: List[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    """Rebuild *vertices* so every edge lies exactly on a 45 ° direction.

    Each edge is snapped to the nearest valid direction, and the polygon is
    reconstructed by walking from the first vertex along the snapped directions.
    The closing edge is dropped if it would create a near-zero-length segment.

    Returns:
        New vertex list with only 45 ° grid-aligned edges.
    """
    if len(vertices) < 3:
        return vertices

    result: List[Tuple[int, int]] = [vertices[0]]
    for i in range(len(vertices)):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % len(vertices)]
        raw_dx = p2[0] - p1[0]
        raw_dy = p2[1] - p1[1]
        if raw_dx == 0 and raw_dy == 0:
            continue
        sx, sy = _snap_direction_to_45(raw_dx, raw_dy)
        # Walk in snapped direction; length = Chebyshev distance
        length = max(abs(raw_dx), abs(raw_dy))
        new_p  = (result[-1][0] + sx * length, result[-1][1] + sy * length)
        # Don't add a duplicate
        if new_p != result[-1] and (len(result) < 2 or new_p != result[0]):
            result.append(new_p)

    # Ensure closure: remove last vertex if it coincides with the first
    if len(result) > 1 and result[-1] == result[0]:
        result.pop()
    return result


# ---------------------------------------------------------------------------
# Private: Grammar helpers
# ---------------------------------------------------------------------------


def _edge_length(poly: List[Tuple[int, int]], idx: int) -> int:
    """Chebyshev length of the edge from ``poly[idx]`` to the next vertex."""
    p1 = poly[idx]
    p2 = poly[(idx + 1) % len(poly)]
    return max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))


def _is_axis_aligned(poly: List[Tuple[int, int]], edge_idx: int) -> bool:
    """True if the edge from poly[edge_idx] to the next vertex is H or V."""
    p1 = poly[edge_idx]
    p2 = poly[(edge_idx + 1) % len(poly)]
    return p1[0] == p2[0] or p1[1] == p2[1]


def _outward_normal(
    p1: Tuple[int, int],
    p2: Tuple[int, int],
) -> Tuple[int, int]:
    """Outward normal of an axis-aligned edge in a y-down clockwise polygon.

    For a clockwise polygon with y increasing downward, the outward normal of
    an edge (p1 → p2) is obtained by rotating the direction vector 90 ° CW:

        normal = (dy, -dx)  where dx = p2.x - p1.x, dy = p2.y - p1.y
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    # Normalise to unit direction then get 90° CW rotation
    if dx != 0:
        dx = dx // abs(dx)
    if dy != 0:
        dy = dy // abs(dy)
    return (dy, -dx)


def _find_eligible_bump_edges(
    poly: List[Tuple[int, int]],
    min_length: int,
) -> List[int]:
    """Indices of axis-aligned edges long enough to accept a bump."""
    return [
        i for i in range(len(poly))
        if _is_axis_aligned(poly, i) and _edge_length(poly, i) >= min_length
    ]


def _find_eligible_notch_edges(
    poly: List[Tuple[int, int]],
    center: Tuple[int, int],
    min_length: int,
    max_depth: int,
) -> List[int]:
    """Axis-aligned edges that face the center and are long enough for a notch.

    We only notch inward; the edge must not already be very close to the
    centre (otherwise the notch would punch through the interior).
    """
    cx, cy = center
    result: List[int] = []
    for i in range(len(poly)):
        if not (_is_axis_aligned(poly, i) and _edge_length(poly, i) >= min_length):
            continue
        p1 = poly[i]
        # Midpoint of this edge
        p2  = poly[(i + 1) % len(poly)]
        mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        dist_to_center = math.hypot(mid[0] - cx, mid[1] - cy)
        if dist_to_center > max_depth + 2:
            result.append(i)
    return result


def _find_eligible_chamfer_corners(poly: List[Tuple[int, int]]) -> List[int]:
    """Indices of vertices that are axis-aligned right-angle corners."""
    eligible: List[int] = []
    n = len(poly)
    for i in range(n):
        prev_p = poly[(i - 1) % n]
        curr   = poly[i]
        next_p = poly[(i + 1) % n]
        # Vectors: incoming and outgoing
        in_dx  = curr[0] - prev_p[0]
        in_dy  = curr[1] - prev_p[1]
        out_dx = next_p[0] - curr[0]
        out_dy = next_p[1] - curr[1]
        # Must both be axis-aligned
        if (in_dx != 0 and in_dy != 0) or (out_dx != 0 and out_dy != 0):
            continue
        # Dot product == 0 → perpendicular (right angle)
        if in_dx * out_dx + in_dy * out_dy == 0:
            eligible.append(i)
    return eligible


def _apply_bump(
    poly: List[Tuple[int, int]],
    edge_idx: int,
    depth: int,
    width: int,
    center: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """Insert a rectangular outward bump on the given axis-aligned edge.

    The bump is centred on the edge midpoint and extends *depth* tiles outward.
    Four new vertices are inserted, splitting the original edge into three
    segments (approach — bump face — departure).

    Returns:
        New poly with the bump inserted.
    """
    p1 = poly[edge_idx]
    p2 = poly[(edge_idx + 1) % len(poly)]
    nx, ny = _outward_normal(p1, p2)

    # Edge direction unit vector
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = max(abs(dx), abs(dy))
    if length == 0:
        return poly
    ux = dx // length
    uy = dy // length

    # Centre offset: bump is centred on the edge midpoint
    mid_frac  = length // 2
    half_bump = width // 2
    start_off = max(1, mid_frac - half_bump)
    end_off   = min(length - 1, mid_frac + half_bump)

    if start_off >= end_off:
        return poly

    # 4 bump vertices
    a = (p1[0] + ux * start_off,             p1[1] + uy * start_off)
    b = (p1[0] + ux * start_off + nx * depth, p1[1] + uy * start_off + ny * depth)
    c = (p1[0] + ux * end_off   + nx * depth, p1[1] + uy * end_off   + ny * depth)
    d = (p1[0] + ux * end_off,               p1[1] + uy * end_off)

    new_poly = poly[:edge_idx + 1] + [a, b, c, d] + poly[edge_idx + 1:]
    return new_poly


def _apply_notch(
    poly: List[Tuple[int, int]],
    edge_idx: int,
    depth: int,
    width: int,
    center: Tuple[int, int],
) -> List[Tuple[int, int]]:
    """Insert a rectangular inward notch on the given axis-aligned edge.

    Same as ``_apply_bump`` but the extrusion direction is *inward* (toward
    the centre).
    """
    p1 = poly[edge_idx]
    p2 = poly[(edge_idx + 1) % len(poly)]
    # Inward = opposite of outward normal
    ox, oy = _outward_normal(p1, p2)
    nx, ny = -ox, -oy

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = max(abs(dx), abs(dy))
    if length == 0:
        return poly
    ux = dx // length
    uy = dy // length

    mid_frac  = length // 2
    half_bump = width // 2
    start_off = max(1, mid_frac - half_bump)
    end_off   = min(length - 1, mid_frac + half_bump)

    if start_off >= end_off:
        return poly

    a = (p1[0] + ux * start_off,             p1[1] + uy * start_off)
    b = (p1[0] + ux * start_off + nx * depth, p1[1] + uy * start_off + ny * depth)
    c = (p1[0] + ux * end_off   + nx * depth, p1[1] + uy * end_off   + ny * depth)
    d = (p1[0] + ux * end_off,               p1[1] + uy * end_off)

    new_poly = poly[:edge_idx + 1] + [a, b, c, d] + poly[edge_idx + 1:]
    return new_poly


def _apply_chamfer(
    poly: List[Tuple[int, int]],
    corner_idx: int,
    cut_size: int,
) -> List[Tuple[int, int]]:
    """Replace a right-angle corner with a single 45 ° diagonal cut.

    The corner vertex is removed and replaced with two new vertices offset
    by *cut_size* tiles along each of the two adjacent edges, producing a
    diagonal segment that is AoE2-valid.

    Returns:
        New poly with the corner chamfered.
    """
    n = len(poly)
    if cut_size < 1 or n < 4:
        return poly

    prev_p = poly[(corner_idx - 1) % n]
    curr   = poly[corner_idx]
    next_p = poly[(corner_idx + 1) % n]

    # Incoming direction (normalised)
    in_dx = curr[0] - prev_p[0]
    in_dy = curr[1] - prev_p[1]
    in_len = max(abs(in_dx), abs(in_dy))
    if in_len == 0:
        return poly
    in_ux = in_dx // in_len
    in_uy = in_dy // in_len

    # Outgoing direction (normalised)
    out_dx = next_p[0] - curr[0]
    out_dy = next_p[1] - curr[1]
    out_len = max(abs(out_dx), abs(out_dy))
    if out_len == 0:
        return poly
    out_ux = out_dx // out_len
    out_uy = out_dy // out_len

    # Ensure cut won't exceed the length of either adjacent edge
    actual_cut = min(cut_size, in_len - 1, out_len - 1)
    if actual_cut < 1:
        return poly

    # New vertices: step back along incoming edge, step forward along outgoing
    a = (curr[0] - in_ux  * actual_cut, curr[1] - in_uy  * actual_cut)
    b = (curr[0] + out_ux * actual_cut, curr[1] + out_uy * actual_cut)

    new_poly = (
        poly[:corner_idx] + [a, b] + poly[corner_idx + 1:]
    )
    return new_poly
