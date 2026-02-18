"""
TODO: Add module description.
"""
from aoe2mapgenerator.map.map_manager import MapManager

import time

# import pytest
# import numpy as np


from aoe2mapgenerator.map.map import Map

# from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
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

    configuration = PlaceGroupsConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.ALFRED_THE_ALPACA,
        player_id=PlayerId.ONE,
        groups=groups,
        group_size=group_size,
    )
    map_manager.place_groups(configuration)

    # Use new Pydantic-style serialization methods
    serialized = map_manager.map.model_dump_json()
    # map_obj: Map = map_manager.map
    # serialized = map_obj.__pydantic_serializer__.to_json(map_obj)
    deserialized = Map.model_validate_json(serialized)
    reserialized = deserialized.model_dump_json()
    
    print("Serialized: " + serialized)
    print("Reserialized: " + reserialized)

    assert serialized == reserialized

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Serialization/deserialization time for {n}x{n} map: {total_time:.4f} seconds")

    # assert (
    #     total_time < 2
    # ), f"Performance test failed: total time {total_time:.4f} seconds"
