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

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.group_placer import GroupPlacerManager
from aoe2mapgenerator.units.placers.point_manager import PointManager


def test_place_groups():
    """
    Tests the creation of a map with size 500.
    """
    n = 200
    start_time = time.time()
    aoe2_map = Map(n)

    point_manager = PointManager()
    group_placer = GroupPlacerManager(aoe2_map)

    point_manager.add_points([(i, j) for i in range(n) for j in range(n)])

    groups = 10
    group_size = 10
    total = groups * group_size

    group_placer.place_groups(
        point_manager=point_manager,
        map_layer_type=MapLayerType.UNIT,
        obj_type=UnitInfo.ALFRED_THE_ALPACA,
        player_id=PlayerId.ONE,
        groups=10,
        group_size=10,
    )

    dictionary = aoe2_map.get_dictionary_from_map_layer_type(MapLayerType.UNIT)

    end_time = time.time()
    total_time = end_time - start_time

    assert len(dictionary[MapObject(UnitInfo.ALFRED_THE_ALPACA, PlayerId.ONE)]) == total

    assert (
        total_time < 1.5
    ), f"Performance test failed: total time {total_time:.4f} seconds"


# def test_create_map_500_benchmark(benchmark):
#     """
#     Tests the creation of a map with size 500.
#     """
#     n = 500
#     benchmark(Map, n)
