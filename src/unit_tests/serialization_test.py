"""
TODO: Add module description.
"""

import time

import pytest
import numpy as np


from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.map.map_manager import MapManager
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.units.placers.placer_configs import PlaceGroupsConfig
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo


def test_serialize():
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

    serialized = map_manager.map.serialize()
    deserialized = Map.deserialize(serialized)
    reserialized = deserialized.serialize()

    assert serialized == reserialized

    end_time = time.time()
    total_time = end_time - start_time

    assert (
        total_time < 2
    ), f"Performance test failed: total time {total_time:.4f} seconds"
