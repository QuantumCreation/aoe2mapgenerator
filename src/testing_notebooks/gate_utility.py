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
    # Generate the polygonal wall points
    points = generate_polygonal_wall(x, y, sides, radius)
    map_manager.point_manager.add_point_collection("wall_points", points)
    map_manager.point_manager.add_point_collection("wall_points_copy", points)

    # Set the type of wall to use
    wall_type = gate_type.get_building_info_wall()

    # Place points for the wall
    map_manager.base_placer.place_multiple(
        map_manager.point_manager.get_point_collection("wall_points"),
        map_layer_type=MapLayerType.UNIT,
        points=points,
        obj_type=wall_type,
        player_id=PlayerId.ONE,
    )

    config = PointSelectorConfig(
        map_layer_type=MapLayerType.UNIT,
        object_type=MapObject(wall_type, player_id=PlayerId.ONE),
    )

    # Get the points for the wall
    points = map_manager.point_manager.point_selector.get_points_from_map_layer(config)

    # Place the gates
    map_manager.gate_placer.place_gate_on_eight_sides(
        point_collection=map_manager.point_manager.get_point_collection(
            "wall_points_2"
        ),
        map_layer_type=MapLayerType.UNIT,
        gate_type=gate_type,
        player_id=PlayerId.ONE,
    )
