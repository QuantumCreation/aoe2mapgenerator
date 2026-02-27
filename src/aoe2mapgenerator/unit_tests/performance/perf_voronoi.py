"""
Benchmarks for VoronoiGenerator and the Poisson disk sampler.

Covers:
- Raw generate_voronoi_l1 at multiple grid/seed scales
- Full Voronoi pipeline (MapManager round-trip)
- _poisson_disk_sample isolation
"""

from __future__ import annotations

import pytest
import numpy as np

from aoe2mapgenerator.units.wallgenerators.voronoi import (
    VoronoiGenerator,
    generate_voronoi_l1,
)
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.placer_configs import VoronoiGeneratorConfig


def _full_point_collection(mm: MapManager, n: int, name: str = "pts"):
    mm.point_manager.add_point_collection(name)
    mm.point_manager.get_point_collection(name).add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )
    return mm.point_manager.get_point_collection(name)


@pytest.mark.benchmark(group="voronoi_l1_raw")
@pytest.mark.parametrize("grid_size,n_seeds", [
    (50,  10),
    (100, 20),
    (200, 50),
    (400, 100),
])
def test_bench_generate_voronoi_l1(benchmark, grid_size: int, n_seeds: int) -> None:
    """Raw vectorised L1 Voronoi grid computation."""
    rng = np.random.default_rng(42)
    seeds = [
        (int(x), int(y))
        for x, y in rng.integers(0, grid_size, size=(n_seeds, 2))
    ]
    benchmark(generate_voronoi_l1, grid_size, grid_size, seeds)


@pytest.mark.benchmark(group="voronoi_pipeline")
@pytest.mark.parametrize("n", [50, 100, 200])
def test_bench_full_voronoi_pipeline(benchmark, n: int) -> None:
    """End-to-end Voronoi zone placement through MapManager."""
    def run() -> None:
        mm = MapManager(n)
        pc = _full_point_collection(mm, n)
        cfg = VoronoiGeneratorConfig(
            point_collection=pc,
            interpoint_distance=max(5, n // 20),
            map_layer_type=MapLayerType.UNIT,
        )
        mm.place_voronoi_zones(cfg)

    benchmark(run)


@pytest.mark.benchmark(group="poisson_disk")
@pytest.mark.parametrize("map_size,radius", [
    (100,  8),
    (200, 10),
    (400, 15),
])
def test_bench_poisson_disk_sample(benchmark, map_size: int, radius: int) -> None:
    """Isolation benchmark for Poisson disk sampler (hot active-list loop)."""
    gen = VoronoiGenerator(Map(size=map_size))
    benchmark(gen._poisson_disk_sample, map_size, map_size, radius, 30)
