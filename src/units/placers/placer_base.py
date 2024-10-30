"""
TODO: Add description.
"""

import random


from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.src.common.enums.enum import (
    MapLayerType,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from aoe2mapgenerator.src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.src.common.enums.enum import AOE2ObjectType
from typing import List
from aoe2mapgenerator.src.units.utils import manhattan_distance
from aoe2mapgenerator.src.map.map_object import MapObject


class PlacerBase:
    """
    Base class for placing objects on a map.
    """

    points_removed_from_point_manager = 0
    points_set_on_map = 0

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map

    def place_closest_to_point(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        starting_point: tuple,
        player_id: PlayerId,
        margin: int = 0,
    ):
        """
        Places an object as close as possible to the starting point.

        Args:
            point_manager (PointManager): The point manager.
            map_layer_type (MapLayerType): The map type.
            obj_type (object): The type of object to be placed.
            starting_point (tuple): The point to place the object.
            player_id (PlayerId): Id of the player for the given object.
            margin (int): Area around the object to be placed.
        """

        points = point_manager.get_point_list()
        search_radius = 5

        points = point_manager.get_nearby_points(starting_point, search_radius)

        for x, y in sorted(
            points,
            key=lambda point: manhattan_distance(point, starting_point),
        ):

            status = self._check_placement(point_manager, (x, y), obj_type, margin)
            if status == CheckPlacementReturnTypes.FAIL:
                return

            self.place_single(
                point_manager,
                map_layer_type,
                (x, y),
                obj_type,
                player_id,
                margin,
            )
            return

    def safe_set_point(
        self,
        point_manager: PointManager,
        point: tuple[int, int],
        obj_type: AOE2ObjectType,
        map_layer_type: MapLayerType,
        player_id: PlayerId,
    ):
        """
        Safely sets a point on the map by removing it from the point manager and updating relevant static variables.
        """
        self.map.set_point(point, obj_type, map_layer_type, player_id)
        PlacerBase.points_set_on_map += 1
        point_manager.remove_point(point)
        PlacerBase.points_removed_from_point_manager += 1

    def place_multiple(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        points: list[tuple[int, int]],
        obj_type: AOE2ObjectType,
        player_id: PlayerId,
        margin: int = 0,
    ):
        """
        places multiple objects at the given points.
        """

        for point in points:
            self.place_single(
                point_manager, map_layer_type, point, obj_type, player_id, margin
            )

    def place_single(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        point: tuple[int, int],
        obj_type: AOE2ObjectType,
        player_id: PlayerId,
        margin: int = 0,
    ) -> dict[str, List[tuple[int, int]]]:
        """
        Places a single object. Assumes placement has already been verified.

        Args:
            map_layer_type_list: The map type.
            point: Point to place base of object.
            obj_type: The type of object to be placed.
            player_id: Id of the player for the given object.
            margin: Area around the object to be placed.
            ghost_margin: Option to include ghost margins, ie. change neighboring squares so nothing can use them.
            height: Height of a given object.
            width: Width of a given object.
        """

        width = ObjectInfo.get_object_width(obj_type)
        height = ObjectInfo.get_object_height(obj_type)
        eff_width = ObjectInfo.get_object_effective_size(obj_type, margin)
        eff_height = ObjectInfo.get_object_effective_size(obj_type, margin)

        x, y = point

        placements: dict[str, List[tuple[int, int]]] = {
            "objects": [],
            "displacements": [],
        }

        # IDK but this if statement may speed things up a little bit. NEEDS TESTING.
        if width > 1 or height > 1 or margin > 0:
            for i in range(-margin, eff_width):
                for j in range(-margin, eff_height):
                    if 0 <= i < width and 0 <= j < height:
                        self.safe_set_point(
                            point_manager,
                            (x + i, y + j),
                            GHOST_OBJECT_DISPLACEMENT_ID,
                            map_layer_type,
                            PlayerId.GAIA,
                        )
                        placements["displacements"].append((x + i, y + j))

        object_placement_point = (x + width // 2, y + height // 2)
        placements["objects"].append(object_placement_point)

        self.safe_set_point(
            point_manager,
            object_placement_point,
            obj_type,
            map_layer_type,
            player_id,
        )

        return placements

    def _check_placement(
        self,
        point_manager: PointManager,
        goal_placement_point: tuple,
        obj_type: AOE2ObjectType = None,
        margin: int = 0,
    ):
        """
        Checks if the given point is a valid placement for an object.

        Args:
            map_layer_type (MapLayerType): The map type.
            point_manager (PointManager): The point manager.
            goal_placement_point (tuple): The point to place the object.
            obj_type (object, optional): The type of object to be placed. Defaults to None.
            margin (int, optional): The margin around the object. Defaults to 0.
            width (int, optional): The width of the object. Defaults to -1.
            height (int, optional): The height of the object. Defaults to -1.
        """

        eff_width = ObjectInfo.get_object_effective_size(obj_type, margin)
        eff_height = ObjectInfo.get_object_effective_size(obj_type, margin)

        x, y = goal_placement_point

        for i in range(-margin, eff_width):
            for j in range(-margin, eff_height):
                if not point_manager.check_point_exists((x + i, y + j)):
                    return CheckPlacementReturnTypes.FAIL

        return CheckPlacementReturnTypes.SUCCESS

    # ---------------------------- SORTING FUNCTIONS ----------------------------

    def default_clumping_func(self, p1, p2, clumping):
        """
        Default clumping function.

        Args:
            p1: First point.
            p2: Second point.
            clumping: Factor to determine how clumped placed objects in a group are.
        """
        if clumping == -1:
            clumping = 999

        distance = (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
        return (distance) + random.random() * (clumping) ** 2
