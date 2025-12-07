import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.units.placers.placer_configs import PlacePathConfig, VisualizeMapConfig
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.units.placers.path_placer import PathPlacer
from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.common.constants.constants import LINUX_PROJECT_UNIT_TEST_IMAGES_PATH
from aoe2mapgenerator.utils.utils import combine_test_name_and_function_name
import os

FILE_NAME = os.path.basename(__file__).replace(".py", "")


def test_create_path(should_visualize):
    n = 200
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    key_points = [(25, 25), (150, 200), (150, 150)]
    num_divisions = [4,8,32,64]
    random_shift_range = [25,15,3,1]

    configuration = PlacePathConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        obj_type=BuildingInfo.CITY_WALL,
        player_id=PlayerId.ONE,
        key_points=key_points,
        num_divisions=num_divisions,
        random_shift_range=random_shift_range,
    )

    path_placer = PathPlacer(map_manager.map)
    path_placer.create_path(configuration)

    values = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.ONE),
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

    assert len(values) > 0
