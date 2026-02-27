"""
Benchmarks for PointCollection spatial queries and bounding-box operations.

Covers:
- get_nearby_points at varying search radii (O(d²) scan before optimisation)
- get_x_point_range / get_y_point_range (O(n) min/max before caching fix)
- add/remove throughput
"""

from __future__ import annotations

import pytest

from aoe2mapgenerator.units.placers.point_management.point_collection import (
    PointCollection,
)


def _make_collection(n: int) -> PointCollection:
    pc = PointCollection()
    pc.add_points([(i, j) for i in range(n) for j in range(n)])
    return pc


@pytest.mark.benchmark(group="nearby_points")
@pytest.mark.parametrize("n,distance", [
    (100,  5),
    (100, 20),
    (200,  5),
    (200, 20),
    (200, 50),
])
def test_bench_get_nearby_points(benchmark, n: int, distance: int) -> None:
    """get_nearby_points — O(d²) dict-lookup scan (Finding 5)."""
    pc = _make_collection(n)
    center = (n // 2, n // 2)
    benchmark(pc.get_nearby_points, center, distance)


@pytest.mark.benchmark(group="bounding_box")
@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_get_x_point_range(benchmark, n: int) -> None:
    """get_x_point_range — O(n) min/max scan before caching (Finding 6)."""
    pc = _make_collection(n)
    benchmark(pc.get_x_point_range)


@pytest.mark.benchmark(group="bounding_box")
@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_get_y_point_range(benchmark, n: int) -> None:
    """get_y_point_range — O(n) min/max scan before caching (Finding 6)."""
    pc = _make_collection(n)
    benchmark(pc.get_y_point_range)


@pytest.mark.benchmark(group="add_remove")
@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_add_remove_points(benchmark, n: int) -> None:
    """Mixed add/remove sequence — measures PointCollection mutation throughput."""
    points = [(i, j) for i in range(n) for j in range(n)]
    quarter = len(points) // 4

    def run() -> None:
        pc = PointCollection()
        pc.add_points(points)
        for p in points[:quarter]:
            pc.remove_point(p)

    benchmark(run)
