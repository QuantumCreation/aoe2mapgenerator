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

from src.common.enums.enum import MapLayerType
from src.map.map import Map
from src.map.map_object import MapObject
from src.units.placers.group_placer import GroupPlacerManager
from src.units.placers.point_management.point_manager import (
    PointCollection,
)
from src.units.placers.placer_configs import PlaceGroupsConfig
from src.map.map_manager import MapManager
from src.units.placers.placer_configs import VisualizeMapConfig
from src.common.constants.constants import (
    LINUX_PROJECT_PATH,
    LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
)
import os
from src.utils.utils import current_function_name, combine_test_name_and_function_name

FILE_NAME = os.path.basename(__file__).replace(".py", "")


def test_place_groups(should_visualize):
    """
    Tests the creation of a map with size 500.
    """
    n = 200
    start_time = time.time()

    map_manager = MapManager(n)

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

    values = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(UnitInfo.ALFRED_THE_ALPACA, PlayerId.ONE),
    )

    if should_visualize:
        # Visualize the map
        visualize_config = VisualizeMapConfig(
            map_layer_type=MapLayerType.UNIT,
            include_zones=True,
            transpose=False,
            save_figure=True,
            file_name=combine_test_name_and_function_name(FILE_NAME),
            file_path=LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
        )

        map_manager.visualize_map(visualize_config)

    end_time = time.time()
    total_time = end_time - start_time

    assert len(values) == total, f"Expected {total} values, got {len(values)}"

    assert (
        total_time < 1.5
    ), f"Performance test failed: total time {total_time:.4f} seconds"
