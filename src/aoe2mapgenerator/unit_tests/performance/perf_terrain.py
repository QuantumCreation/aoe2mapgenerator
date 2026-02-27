"""
Benchmarks for PerlinTerrainGenerator.

Covers:
- generate_noise_matrix at multiple sizes (the pure-Python inner loop hotspot)
- generate_perlin_terrain end-to-end
"""

from __future__ import annotations

import pytest

from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.terrain.terrain import (
    PerlinNoiseConfig,
    PerlinTerrainConfig,
    PerlinTerrainGenerator,
)


@pytest.mark.benchmark(group="noise_matrix")
@pytest.mark.parametrize("w,h", [
    (50,   50),
    (100, 100),
    (200, 200),
    (400, 400),
])
def test_bench_generate_noise_matrix(benchmark, w: int, h: int) -> None:
    """Benchmark noise-matrix generation (pure-Python nested loops before fix)."""
    gen = PerlinTerrainGenerator(Map(size=max(w, h)))
    cfg = PerlinNoiseConfig(seed=0, scale=24.0, octaves=4)
    benchmark(gen.generate_noise_matrix, w, h, cfg)


@pytest.mark.benchmark(group="perlin_terrain_e2e")
@pytest.mark.parametrize("n", [50, 100, 200])
def test_bench_generate_perlin_terrain_e2e(benchmark, n: int) -> None:
    """End-to-end terrain + elevation write into the map."""
    def run() -> None:
        aoe_map = Map(size=n)
        gen = PerlinTerrainGenerator(aoe_map)
        cfg = PerlinTerrainConfig(
            noise=PerlinNoiseConfig(seed=42, scale=24.0, octaves=4),
            min_elevation=0,
            max_elevation=7,
        )
        gen.generate_perlin_terrain(cfg)

    benchmark(run)
