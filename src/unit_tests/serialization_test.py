"""
TODO: Add module description.
"""
from src.map.map_manager import MapManager

import time

# import pytest
# import numpy as np


from src.map.map import Map

# from src.map.map_object import MapObject
from src.common.enums.enum import MapLayerType
from src.units.placers.placer_configs import PlaceGroupsConfig
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo

def test_serialize():
    """
    Tests the creation of a map with size 500.
    """
    n = 200
    

    map_manager = MapManager(n)

    # Skip the initialization of the map
    start_time = time.time()
    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    groups = 10
    group_size = 10
    total = groups * group_size

    configuration = PlaceGroupsConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
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
