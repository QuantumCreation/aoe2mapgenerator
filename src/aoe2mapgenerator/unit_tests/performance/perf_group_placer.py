"""
Benchmarks for GroupPlacer and PlacerBase.fill().

Covers:
- place_groups at various group counts and sizes
- PlacerBase.fill() for full-layer coverage
"""

from __future__ import annotations

import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.units.placers.placer_configs import FillConfig, PlaceGroupsConfig


def _make_manager_with_points(n: int) -> tuple[MapManager, object]:
    mm = MapManager(n)
    mm.point_manager.add_point_collection("pts")
    mm.point_manager.get_point_collection("pts").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )
    return mm, mm.point_manager.get_point_collection("pts")


@pytest.mark.benchmark(group="place_groups")
@pytest.mark.parametrize("n,groups,group_size", [
    (100,  50, 10),
    (200, 200, 20),
    (200, 500,  5),
])
def test_bench_place_groups(benchmark, n: int, groups: int, group_size: int) -> None:
    """Benchmark place_groups at varying densities."""
    def run() -> None:
        mm, pc = _make_manager_with_points(n)
        cfg = PlaceGroupsConfig(
            object_type=UnitInfo.MILITIA,
            map_layer_type=MapLayerType.UNIT,
            point_collection=pc,
            groups=groups,
            group_size=group_size,
            player_id=PlayerId.ONE,
            margin=0,
            clumping=0,
        )
        mm.place_groups(cfg)

    benchmark(run)


@pytest.mark.benchmark(group="fill")
@pytest.mark.parametrize("n", [100, 200])
def test_bench_fill(benchmark, n: int) -> None:
    """Benchmark fill() over an entire layer."""
    def run() -> None:
        mm, pc = _make_manager_with_points(n)
        cfg = FillConfig(
            obj_type=TerrainId.GRASS_2,
            map_layer_type=MapLayerType.TERRAIN,
            point_collection=pc,
            player_id=PlayerId.GAIA,
            margin=0,
        )
        mm._base_placer.fill(cfg)

    benchmark(run)
