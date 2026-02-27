"""
Benchmarks for MapLayer mutation throughput.

Covers:
- set_point() sequential write throughput
- MapLayer construction cost (list-of-lists + dict init)
"""

from __future__ import annotations

import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.maplayer import MapLayer


@pytest.mark.benchmark(group="maplayer_set_point")
@pytest.mark.parametrize("n", [50, 100, 200, 400])
def test_bench_set_point_sequential(benchmark, n: int) -> None:
    """Sequential set_point across every tile — measures mutation throughput."""
    layer = MapLayer(map_layer_type=MapLayerType.TERRAIN, size=n)

    def run() -> None:
        for i in range(n):
            for j in range(n):
                layer.set_point((i, j), TerrainId.GRASS_2, PlayerId.GAIA)

    benchmark(run)


@pytest.mark.benchmark(group="maplayer_init")
@pytest.mark.parametrize("n", [50, 100, 200, 400])
def test_bench_maplayer_init(benchmark, n: int) -> None:
    """MapLayer construction — list-of-lists allocation + dict creation."""
    benchmark(MapLayer, map_layer_type=MapLayerType.TERRAIN, size=n)
