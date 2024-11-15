from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.players import PlayerId
from src.common.enums.enum import (
    MapLayerType,
    GateType,
)
from src.map.map_manager import MapManager
from src.units.placers.placer_configs import PointSelectorConfig
from src.map.map_object import MapObject
from src.units.wallgenerators.polygon import generate_polygonal_wall


def generate_polygon_walls_with_gates(
    map_manager: MapManager,
    x: int,
    y: int,
    sides: int,
    radius: int,
    gate_type: GateType,
):
    """
    Generates a polygonal wall with gates.

    Args:
        map_manager (MapManager): The map manager.
        x (int): The x coordinate.
        y (int): The y coordinate.
        gate_type (GateType): The type of gate.
    """
    points = generate_polygonal_wall(x, y, sides, radius)
    wp_name, wpc_name = add_wall_points(map_manager, points)
    wall_type = gate_type.get_building_info_wall()
    place_wall_points(map_manager, wp_name, points, wall_type)
    place_gates(map_manager, wpc_name, gate_type)


def add_wall_points(map_manager: MapManager, points: list) -> tuple:
    wp_name = map_manager.point_manager.add_point_collection(
        "wall_points", points, True
    )
    wpc_name = map_manager.point_manager.add_point_collection(
        "wall_points_copy", points, True
    )
    return wp_name, wpc_name


def place_wall_points(
    map_manager: MapManager, wp_name: str, points: list, wall_type: str
):
    map_manager.base_placer.place_multiple(
        map_manager.point_manager.get_point_collection(wp_name),
        map_layer_type=MapLayerType.UNIT,
        points=points,
        obj_type=wall_type,
        player_id=PlayerId.ONE,
    )


def place_gates(map_manager: MapManager, wpc_name: str, gate_type: GateType):
    map_manager.gate_placer.place_gate_on_eight_sides(
        point_collection=map_manager.point_manager.get_point_collection(wpc_name),
        map_layer_type=MapLayerType.UNIT,
        gate_type=gate_type,
        player_id=PlayerId.ONE,
    )
