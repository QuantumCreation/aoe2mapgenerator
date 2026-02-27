"""
End-to-end map generation benchmarks.

These are the top-level regression guards: Voronoi zone assignment + group
placement over the full map at realistic sizes.  A ≥50% mean-time regression
on any test here should block CI (use --benchmark-compare-fail=mean:50%).
"""

from __future__ import annotations

import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceGroupsConfig,
    VoronoiGeneratorConfig,
)


@pytest.mark.benchmark(group="full_map")
@pytest.mark.parametrize("n", [50, 100, 200])
def test_bench_full_map_generation(benchmark, n: int) -> None:
    """
    Realistic scenario: Voronoi zones + group placement across the full map.

    This is the primary end-to-end regression guard.  A ≥50% slowdown here
    must fail CI.
    """
    def run() -> None:
        mm = MapManager(n)
        mm.point_manager.add_point_collection("all")
        mm.point_manager.get_point_collection("all").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )
        pc = mm.point_manager.get_point_collection("all")

        vcfg = VoronoiGeneratorConfig(
            point_collection=pc,
            interpoint_distance=max(5, n // 20),
            map_layer_type=MapLayerType.ZONE,
        )
        mm.place_voronoi_zones(vcfg)

        gcfg = PlaceGroupsConfig(
            object_type=UnitInfo.MILITIA,
            map_layer_type=MapLayerType.UNIT,
            point_collection=pc,
            groups=min(200, n * n // 50),
            group_size=5,
            player_id=PlayerId.ONE,
            margin=0,
            clumping=0,
        )
        mm.place_groups(gcfg)

    benchmark(run)


@pytest.mark.benchmark(group="map_init")
@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_map_manager_init(benchmark, n: int) -> None:
    """MapManager construction time (5 MapLayer allocs + dict creation)."""
    benchmark(MapManager, n)
