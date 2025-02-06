from typing import List, Tuple
from AoE2ScenarioParser.datasets.players import PlayerId
from src.common.enums.enum import (
    MapLayerType,
    GateType,
)
from src.map.map_manager import MapManager
from src.units.placers.placer_configs import PointSelectorConfig
from src.units.placers.point_management.point_collection import PointCollection
from src.map.map_object import MapObject
from src.units.wallgenerators.polygon import generate_polygonal_wall_points
from AoE2ScenarioParser.datasets.buildings import BuildingInfo


def generate_polygon_walls_with_gates(
    map_manager: MapManager,
    point_collection: PointCollection,
    point: Tuple[int, int],
    sides: int,
    radius: float,
    gate_type: GateType,
    player_id: PlayerId = PlayerId.ONE,
) -> None:
    """
    Generates a polygonal wall with gates.

    Args:
        map_manager (MapManager): The map manager.
        x (int): The x coordinate.
        y (int): The y coordinate.
        sides (int): The number of sides of the polygon.
        radius (int): The radius of the polygon.
        gate_type (GateType): The type of gate.
    """
    points: List[Tuple[int, int]] = generate_polygonal_wall_points(point, sides, radius)

    wall_point_collection: PointCollection = (
        map_manager.point_manager.add_point_collection("wall_points", points, True)
    )

    intersection_points: PointCollection = point_collection.intersect(
        wall_point_collection
    )

    intersection_points_editable: PointCollection = intersection_points.copy()

    wall_type: BuildingInfo = gate_type.get_building_info_wall()
    place_wall_points(map_manager, point_collection, points, wall_type, player_id)
    place_gates(map_manager, intersection_points_editable, gate_type, player_id)


def place_wall_points(
    map_manager: MapManager,
    wp_collection: PointCollection,
    points: List[Tuple[int, int]],
    wall_type: str,
    player_id: PlayerId = PlayerId.ONE,
) -> None:
    for point in points:
        map_manager.base_placer.place_if_possible(
            point_collection=wp_collection,
            map_layer_type=MapLayerType.UNIT,
            obj_type=wall_type,
            starting_point=point,
            player_id=player_id,
        )


def place_gates(
    map_manager: MapManager,
    point_collection: PointCollection,
    gate_type: GateType,
    player_id: PlayerId = PlayerId.ONE,
) -> None:
    map_manager.gate_placer.place_gate_on_eight_sides(
        point_collection=point_collection,
        map_layer_type=MapLayerType.UNIT,
        gate_type=gate_type,
        player_id=player_id,
    )
