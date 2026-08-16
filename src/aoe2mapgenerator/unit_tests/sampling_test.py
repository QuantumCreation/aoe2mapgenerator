"""
Tests for the pure sampling utilities (jittered_grid, poisson_disk,
space_colonization).
"""

import math

import numpy as np

from aoe2mapgenerator.utils.sampling import (
    jittered_grid,
    poisson_disk,
    space_colonization,
)


def test_jittered_grid_deterministic():
    a = jittered_grid(0, 0, 10, 10, cell=2, jitter=0.5, rng=42)
    b = jittered_grid(0, 0, 10, 10, cell=2, jitter=0.5, rng=42)
    assert a == b


def test_jittered_grid_within_bounds():
    pts = jittered_grid(0, 0, 20, 20, cell=3, jitter=1.0, rng=1)
    assert pts, "expected at least one point"
    for x, y in pts:
        assert 0 <= x < 20
        assert 0 <= y < 20


def test_jittered_grid_zero_jitter_is_grid():
    pts = jittered_grid(0, 0, 12, 12, cell=3, jitter=0.0, rng=0)
    # With zero jitter every point sits exactly on the grid lines.
    for x, y in pts:
        assert x % 3 == 0
        assert y % 3 == 0


def test_poisson_disk_respects_min_distance():
    pts = poisson_disk(0, 0, 40, 40, min_dist=5.0, rng=7)
    assert len(pts) >= 2, "expected multiple points"
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
            assert d >= 5.0 - 1e-9, f"points {pts[i]} and {pts[j]} too close: {d}"


def test_poisson_disk_deterministic():
    a = poisson_disk(0, 0, 30, 30, min_dist=4.0, rng=99)
    b = poisson_disk(0, 0, 30, 30, min_dist=4.0, rng=99)
    assert a == b


def test_poisson_disk_max_points():
    pts = poisson_disk(0, 0, 60, 60, min_dist=2.0, max_points=5, rng=3)
    assert len(pts) <= 5


def test_poisson_disk_empty_region():
    assert poisson_disk(10, 10, 5, 5, min_dist=1.0, rng=1) == []


def test_space_colonization_reaches_all_targets():
    targets = [(10, 10), (30, 10), (20, 30)]
    seeds = [(20, 20)]
    occupied = set(space_colonization(targets, seeds, max_steps=500, rng=0))
    for t in targets:
        assert t in occupied, f"target {t} not reached"


def test_space_colonization_includes_seeds():
    seeds = [(5, 5), (15, 15)]
    occupied = set(space_colonization([(20, 20)], seeds, max_steps=200, rng=0))
    for s in seeds:
        assert s in occupied


def test_space_colonization_no_seeds():
    assert space_colonization([(10, 10)], [], rng=0) == []
