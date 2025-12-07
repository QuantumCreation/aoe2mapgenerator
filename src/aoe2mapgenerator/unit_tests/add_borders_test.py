"""
Tests adding borders to a map.
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.placer_configs import (
    VoronoiGeneratorConfig,
    AddBordersConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.units.placers.placer_configs import VisualizeMapConfig
from aoe2mapgenerator.common.constants.constants import (
    LINUX_PROJECT_PATH,
    LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
)
import os
import pytest
from aoe2mapgenerator.utils.utils import current_function_name, combine_test_name_and_function_name

FILE_NAME = os.path.basename(__file__).replace(".py", "")


def test_border(should_visualize):
    """
    Tests the creation of a map with size 500.
    """

    n = 10
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    configuration = AddBordersConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        obj_type=BuildingInfo.CITY_WALL,
        player_id=PlayerId.THREE,
    )

    map_manager.place_borders(configuration)

    values = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.THREE),
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

    assert len(values) == 36


def test_border_2(should_visualize):
    """
    Tests the creation of a map with size 500.
    """

    n = 10
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    configuration = AddBordersConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        obj_type=BuildingInfo.CITY_WALL,
        player_id=PlayerId.THREE,
        border_width=2,
    )

    map_manager.place_borders(configuration)

    values = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.THREE),
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

    assert len(values) == 64
