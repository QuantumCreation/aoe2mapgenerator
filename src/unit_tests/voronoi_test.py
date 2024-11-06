"""
Tests the voronoi algorithm.
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.map.map_manager import MapManager
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.units.placers.placer_configs import VoronoiGeneratorConfig
from aoe2mapgenerator.src.units.placers.point_management.point_manager import (
    PointCollection,
)


def test_voronoi():
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

    assert len(zones) > 3
