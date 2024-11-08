"""
Tests adding borders to a map.
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo

from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.map.map_manager import MapManager
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.units.placers.placer_configs import (
    VoronoiGeneratorConfig,
    AddBordersConfig,
)
from aoe2mapgenerator.src.units.placers.point_management.point_manager import (
    PointCollection,
)


def test_border():
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

    assert len(values) == 36


def test_border_2():
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
        margin=2,
    )

    map_manager.place_borders(configuration)

    values = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.THREE),
    )

    assert len(values) == 64
