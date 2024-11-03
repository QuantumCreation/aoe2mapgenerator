"""
TODO: Add module description.
"""

import time

import pytest
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.units.placers.group_placer import GroupPlacerManager
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from aoe2mapgenerator.src.units.placers.placer_configs import PlaceGroupsConfig
from aoe2mapgenerator.src.map.map_manager import MapManager


def test_place_groups():
    """
    Tests the creation of a map with size 500.
    """
    n = 200
    start_time = time.time()

    map_manager = MapManager(n)

    point_manager = PointManager()
    point_manager.add_points([(i, j) for i in range(n) for j in range(n)])

    groups = 10
    group_size = 10
    total = groups * group_size

    configuration = PlaceGroupsConfig(
        point_manager=point_manager,
        map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.ALFRED_THE_ALPACA,
        player_id=PlayerId.ONE,
        groups=groups,
        group_size=group_size,
    )
    map_manager.place_groups(configuration)

    values = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(UnitInfo.ALFRED_THE_ALPACA, PlayerId.ONE),
    )

    end_time = time.time()
    total_time = end_time - start_time

    assert len(values) == total

    assert (
        total_time < 1.5
    ), f"Performance test failed: total time {total_time:.4f} seconds"


# def test_create_map_500_benchmark(benchmark):
#     """
#     Tests the creation of a map with size 500.
#     """
#     n = 500
#     benchmark(Map, n)
