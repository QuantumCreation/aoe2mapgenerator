"""
Tests the voronoi algorithm.
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.placer_configs import VoronoiGeneratorConfig
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.units.placers.placer_configs import VisualizeMapConfig
from aoe2mapgenerator.common.constants.constants import (
    LINUX_PROJECT_PATH,
    LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
)
import os
from aoe2mapgenerator.utils.utils import current_function_name, combine_test_name_and_function_name

FILE_NAME = os.path.basename(__file__).replace(".py", "")


def test_voronoi(should_visualize):
    """
    Tests the creation of a map with size 500.
    """

    n = 50
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    configuration = VoronoiGeneratorConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        interpoint_distance=10,
        map_layer_type=MapLayerType.UNIT,
    )

    zones = map_manager.place_voronoi_zones(configuration)

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

    assert len(zones) > 3
