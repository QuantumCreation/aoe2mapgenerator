from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection
from aoe2mapgenerator.units.placers.point_management.point_manager import PointManager


def test_filter_by_distance_uses_symmetric_euclidean_radius() -> None:
    pc = PointCollection()
    points = [
        (0, 0),
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]
    pc.add_points(points)

    filtered = pc.filter_by_distance((0, 0), distance=1)

    assert set(filtered.get_point_list()) == {
        (0, 0),
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    }


def test_get_maximal_points_returns_bottommost_as_fourth_value() -> None:
    pc = PointCollection()
    pc.add_points([(2, 5), (1, 3), (4, 4), (6, 2)])

    left, right, top, bottom = pc.get_maximal_points()

    assert left == (6, 2)
    assert right == (2, 5)
    assert top == (1, 3)
    assert bottom == (6, 2)


def test_get_collection_from_terrain_finds_points_and_respects_occupancy() -> None:
    aoe2_map = Map(size=5)
    aoe2_map.set_point((1, 1), TerrainId.DESERT_SAND, MapLayerType.TERRAIN, PlayerId.GAIA)
    aoe2_map.set_point((2, 2), TerrainId.DESERT_SAND, MapLayerType.TERRAIN, PlayerId.GAIA)
    aoe2_map.set_point((4, 4), TerrainId.SHALLOWS, MapLayerType.TERRAIN, PlayerId.GAIA)

    # Occupy one of the grass tiles on the unit layer.
    aoe2_map.set_point((2, 2), OtherInfo.STONE_MINE, MapLayerType.UNIT, PlayerId.GAIA)

    point_manager = PointManager(aoe2_map)

    all_desert = point_manager.get_collection_from_terrain(
        TerrainId.DESERT_SAND,
        exclude_occupied=False,
    )
    unoccupied_desert = point_manager.get_collection_from_terrain(
        TerrainId.DESERT_SAND,
        exclude_occupied=True,
    )

    assert set(all_desert.get_point_list()) == {(1, 1), (2, 2)}
    assert set(unoccupied_desert.get_point_list()) == {(1, 1)}
