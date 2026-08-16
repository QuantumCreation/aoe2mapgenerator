"""Pure sampling utilities for procedural map generation.

These functions answer the "where do things go?" question. They are **pure**:
given the same region, count, and RNG they always return the same points, which
makes them trivially unit-testable and reusable by every template.

All functions take an explicit ``rng`` (a ``numpy.random.Generator``) so callers
control determinism. Pass ``np.random.default_rng(seed)`` for reproducible
output.

Coordinate convention: points are ``(x, y)`` tuples where ``x`` is the column
and ``y`` is the row, matching the rest of the library.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

Point = tuple[int, int]


def _as_generator(rng: np.random.Generator | int | None) -> np.random.Generator:
    """Coerce an int seed or None into a fresh ``numpy.random.Generator``."""
    if isinstance(rng, np.random.Generator):
        return rng
    return np.random.default_rng(rng)


def jittered_grid(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    cell: int = 1,
    jitter: float = 0.5,
    rng: np.random.Generator | int | None = None,
) -> list[Point]:
    """Return a grid of points with a random offset added to each cell.

    Even coverage with organic irregularity — the default scatter for trees,
    berry bushes, and farm placement.

    Args:
        x0, y0: Inclusive top-left corner of the region.
        x1, y1: Exclusive bottom-right corner of the region.
        cell: Grid spacing in tiles.
        jitter: Maximum offset as a fraction of ``cell`` (0 = perfect grid,
            1 = up to a full cell of offset).
        rng: RNG or seed.

    Returns:
        List of ``(x, y)`` points, clamped to the region.
    """
    rng = _as_generator(rng)
    if cell < 1:
        raise ValueError("cell must be >= 1")

    points: list[Point] = []
    xs = range(x0, x1, cell)
    ys = range(y0, y1, cell)
    for x in xs:
        for y in ys:
            ox = rng.uniform(-jitter, jitter) * cell
            oy = rng.uniform(-jitter, jitter) * cell
            px = int(round(x + ox))
            py = int(round(y + oy))
            # Clamp into the region so jitter never pushes points out.
            px = max(x0, min(x1 - 1, px))
            py = max(y0, min(y1 - 1, py))
            points.append((px, py))
    return points


def poisson_disk(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    min_dist: float,
    max_points: int | None = None,
    rng: np.random.Generator | int | None = None,
    max_attempts: int = 30,
) -> list[Point]:
    """Return points with a guaranteed minimum pairwise distance (Bridson's).

    Organic evenness with no overlaps — the right sampler for building
    placement inside cities/villages.

    Args:
        x0, y0: Inclusive top-left corner.
        x1, y1: Exclusive bottom-right corner.
        min_dist: Minimum Euclidean distance between any two points.
        max_points: Optional cap on the number of points returned.
        rng: RNG or seed.
        max_attempts: Per-point retry budget before giving up on a cell.

    Returns:
        List of ``(x, y)`` points.
    """
    rng = _as_generator(rng)
    if min_dist <= 0:
        raise ValueError("min_dist must be > 0")

    width = x1 - x0
    height = y1 - y0
    if width <= 0 or height <= 0:
        return []

    # Grid cell size is min_dist / sqrt(2) so each cell holds at most one point.
    cell_size = min_dist / math.sqrt(2.0)
    grid_w = max(1, math.ceil(width / cell_size))
    grid_h = max(1, math.ceil(height / cell_size))
    grid: list[list[int]] = [[-1] * grid_w for _ in range(grid_h)]

    points: list[Point] = []
    active: list[int] = []  # indices into `points` of points still being expanded

    def _add(x: int, y: int) -> int:
        idx = len(points)
        points.append((x, y))
        active.append(idx)
        gx = int((x - x0) // cell_size)
        gy = int((y - y0) // cell_size)
        grid[gy][gx] = idx
        return idx

    def _too_close(x: int, y: int) -> bool:
        gx = int((x - x0) // cell_size)
        gy = int((y - y0) // cell_size)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < grid_w and 0 <= ny < grid_h:
                    idx = grid[ny][nx]
                    if idx != -1:
                        px, py = points[idx]
                        if (px - x) ** 2 + (py - y) ** 2 < min_dist * min_dist:
                            return True
        return False

    # Seed with a random point.
    _add(int(rng.integers(x0, x1)), int(rng.integers(y0, y1)))

    while active and (max_points is None or len(points) < max_points):
        idx = int(rng.integers(0, len(active)))
        px, py = points[idx]
        placed = False
        for _ in range(max_attempts):
            # Sample in an annulus [2r, 3r] around the active point.
            angle = rng.uniform(0.0, 2.0 * math.pi)
            radius = min_dist * rng.uniform(2.0, 3.0)
            nx = int(round(px + radius * math.cos(angle)))
            ny = int(round(py + radius * math.sin(angle)))
            if x0 <= nx < x1 and y0 <= ny < y1 and not _too_close(nx, ny):
                _add(nx, ny)
                placed = True
                break
        if not placed:
            active.pop(idx)

    return points


def space_colonization(
    targets: Sequence[Point],
    seeds: Sequence[Point],
    max_steps: int = 200,
    rng: np.random.Generator | int | None = None,
) -> list[Point]:
    """Grow a tree from ``seeds`` toward evenly spaced ``targets`` (SCA).

    Produces the "organic medieval road" look: a branching tree that reaches
    every target. Returns the set of occupied tiles (the road network).

    Args:
        targets: Destination points the tree must reach (buildings, map edges).
        seeds: Starting points of the tree (settlement center, map border).
        max_steps: Safety cap on growth iterations.
        rng: RNG or seed. Reserved for future tie-breaking; the current greedy
            algorithm is deterministic without it.

    Returns:
        List of ``(x, y)`` tiles occupied by the grown tree.
    """
    if not seeds:
        return []

    occupied: set[Point] = set(seeds)
    remaining: list[Point] = list(targets)

    # Greedy nearest-target connection: repeatedly pick the (target, tree-cell)
    # pair with the smallest distance and grow a path between them. This yields
    # a connected tree that reaches every target (a greedy Steiner-like
    # network), which is exactly the "organic road" shape we want.
    while remaining:
        best_pair: tuple[Point, Point] | None = None
        best_d = float("inf")
        for t in remaining:
            for c in occupied:
                d = (t[0] - c[0]) ** 2 + (t[1] - c[1]) ** 2
                if d < best_d:
                    best_d = d
                    best_pair = (t, c)
        if best_pair is None:
            break
        target, start = best_pair

        # Grow a one-tile-at-a-time path from `start` to `target`.
        cur = start
        for _ in range(max_steps):
            if cur == target:
                break
            dx = target[0] - cur[0]
            dy = target[1] - cur[1]
            if abs(dx) >= abs(dy):
                step = (cur[0] + (1 if dx > 0 else -1), cur[1])
            else:
                step = (cur[0], cur[1] + (1 if dy > 0 else -1))
            if step in occupied:
                # Blocked straight ahead; try the perpendicular axis.
                if abs(dx) >= abs(dy):
                    step = (cur[0], cur[1] + (1 if dy > 0 else -1))
                else:
                    step = (cur[0] + (1 if dx > 0 else -1), cur[1])
                if step in occupied:
                    break  # fully stuck; give up on this target
            occupied.add(step)
            cur = step

        remaining.remove(target)

    return list(occupied)
