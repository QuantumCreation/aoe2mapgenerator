from typing import List, Tuple
from AoE2ScenarioParser.datasets.players import PlayerId
from src.common.enums.enum import (
    MapLayerType,
    GateType,
)
from src.map.map_manager import MapManager
from src.units.placers.placer_configs import PointSelectorConfig, PlaceIfPossibleConfig
from src.units.placers.point_management.point_collection import PointCollection
from src.map.map_object import MapObject
from src.units.wallgenerators.polygon import generate_polygonal_wall_points
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from src.units.placers.placer_base import PlacerBase
from src.map.map_manager import IMapManager


class AdvancedWallPlacer(PlacerBase):
    
    def generate_polygon_walls_with_gates(
        self,
        map_manager: IMapManager,
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
            point_collection (PointCollection): The point collection.
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
        self.place_wall_points(map_manager, point_collection, points, wall_type, player_id)
        self.place_gates(map_manager, intersection_points_editable, gate_type, player_id)


    def place_wall_points(
        self,
        map_manager: IMapManager,
        wp_collection: PointCollection,
        points: List[Tuple[int, int]],
        wall_type: str,
        player_id: PlayerId = PlayerId.ONE,
    ) -> None:
        for point in points:
            config = PlaceIfPossibleConfig(
                point_collection=wp_collection,
                map_layer_type=MapLayerType.UNIT,
                obj_type=wall_type,
                starting_point=point,
                player_id=player_id,
            )
            self.place_if_possible(config)


    def place_gates(
        self,
        map_manager: IMapManager,
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

def get_points_inside_polygon(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Get all points inside the polygon defined by the given points.

    Args:
        points (List[Tuple[int, int]]): The points defining the polygon.

    Returns:
        List[Tuple[int, int]]: The points inside the polygon.
    """
    from matplotlib.path import Path
    import numpy as np

    polygon_path = Path(points)
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)

    grid_x, grid_y = np.meshgrid(np.arange(min_x, max_x + 1), np.arange(min_y, max_y + 1))
    grid_points = np.vstack((grid_x.flatten(), grid_y.flatten())).T

    inside_mask = polygon_path.contains_points(grid_points)
    inside_points = grid_points[inside_mask]

    return [tuple(point) for point in inside_points]
