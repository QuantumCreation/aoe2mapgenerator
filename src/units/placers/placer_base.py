"""
TODO: Add description.
"""

import random


from AoE2ScenarioParser.datasets.players import PlayerId

from src.common.enums.enum import (
    MapLayerType,
    CheckPlacementReturnTypes,
)
from src.units.placers.point_management.point_collection import (
    PointCollection,
)
from src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from src.map.map import Map
from src.units.placers.object_info import ObjectInfo
from src.common.types import AOE2ObjectType
from typing import List
from src.units.utils import manhattan_distance
from src.map.map_object import MapObject
from src.common.types import Point
from src.units.placers.point_management.points_returned import PointPlacementResults


class PlacerBase:
    """
    Base class for placing objects on a map.
    """

    points_removed_from_point_collection = 0
    points_set_on_map = 0

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map
        self.point_placement_record = PointPlacementResults()

    def place_closest_to_point(
        self,
        point_collection: PointCollection,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        starting_point: tuple,
        player_id: PlayerId,
        margin: int = 0,
    ) -> None:
        """
        Places an object as close as possible to the starting point, while still being a valid placement.
        Searches through nearby points within the point collection to find a valid placement.

        Args:
            point_collection (PointCollection): The point manager.
            map_layer_type (MapLayerType): The map type.
            obj_type (object): The type of object to be placed.
            starting_point (tuple): The point to place the object.
            player_id (PlayerId): Id of the player for the given object.
            margin (int): Area around the object to be placed.
        """

        points: List[Point] = point_collection.get_point_list()
        search_radius = 5

        points = point_collection.get_nearby_points(starting_point, search_radius)

        for x, y in sorted(
            points,
            key=lambda point: manhattan_distance(point, starting_point),
        ):

            status = self._check_placement(point_collection, (x, y), obj_type, margin)
            if status == CheckPlacementReturnTypes.FAIL:
                continue

            self._place_single(
                point_collection,
                map_layer_type,
                (x, y),
                obj_type,
                player_id,
                margin,
            )
            return

    def place_if_possible(
        self,
        point_collection: PointCollection,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        starting_point: Point,
        player_id: PlayerId,
        margin: int = 0,
    ) -> None:
        """
        Places an object if a valid placement exists.

        Args:
            point_collection (PointCollection): The point manager.
            map_layer_type (MapLayerType): The map type.
            obj_type (object): The type of object to be placed.
            player_id (PlayerId): Id of the player for the given object.
            margin (int): Area around the object to be placed.
        """

        status = self._check_placement(
            point_collection, starting_point, obj_type, margin
        )

        if status == CheckPlacementReturnTypes.SUCCESS:
            self._place_single(
                point_collection,
                map_layer_type,
                starting_point,
                obj_type,
                player_id,
                margin,
            )
            return

    def place_multiple(
        self,
        point_collection: PointCollection,
        map_layer_type: MapLayerType,
        points: list[tuple[int, int]],
        obj_type: AOE2ObjectType,
        player_id: PlayerId,
        margin: int = 0,
    ) -> None:
        """
        places multiple objects at the given points. Does not check for safe placement.

        Args:
            point_collection: The point manager.
            map_layer_type: The map type.
            points: Points to place objects.
            obj_type: The type of object to be placed.
            player_id: Id of the player for the given object.
            margin: Area around the object to be placed.
        """

        for point in points:
            self._place_single(
                point_collection, map_layer_type, point, obj_type, player_id, margin
            )

        return

    def fill(
        self,
        point_collection: PointCollection,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        player_id: PlayerId,
        margin: int = 0,
    ) -> None:
        """
        Fills the entire point collection with the given object.

        Args:
            point_collection: The point manager.
            map_layer_type: The map type.
            obj_type: The type of object to be placed.
            player_id: Id of the player for the given object.
            margin: Area around the object to be placed.
        """

        for point in point_collection.get_point_list_copy():
            status = self._check_placement(point_collection, point, obj_type, margin)
            if status == CheckPlacementReturnTypes.SUCCESS:
                self._place_single(
                    point_collection, map_layer_type, point, obj_type, player_id, margin
                )

    def _place_single(
        self,
        point_collection: PointCollection,
        map_layer_type: MapLayerType,
        point: tuple[int, int],
        obj_type: AOE2ObjectType,
        player_id: PlayerId,
        margin: int = 0,
    ) -> None:
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

        rows = ObjectInfo.get_object_rows(obj_type)
        columns = ObjectInfo.get_object_columns(obj_type)
        eff_rows = ObjectInfo.get_object_effective_size(obj_type, margin)
        eff_columns = ObjectInfo.get_object_effective_size(obj_type, margin)

        row_x, row_y = point
        x_shift, y_shift = rows // 2, columns // 2

        # Place the ghost objects since we only need to set one square to place
        # objects which take up more than one square of space
        for i in range(-margin, eff_rows):
            for j in range(-margin, eff_columns):
                if (
                    0 - x_shift <= i - x_shift < rows
                    and 0 - y_shift <= j - y_shift < columns
                ):
                    shifted_point = (row_x + i - x_shift, row_y + j - y_shift)
                    self.__set_point_and_track_changes(
                        point_collection,
                        shifted_point,
                        GHOST_OBJECT_DISPLACEMENT_ID,
                        map_layer_type,
                        PlayerId.GAIA,
                    )

        object_placement_point = (
            row_x + rows // 2 - x_shift,
            row_y + columns // 2 - y_shift,
        )

        self.__set_point_and_track_changes(
            point_collection,
            object_placement_point,
            obj_type,
            map_layer_type,
            player_id,
        )

    def _check_placement(
        self,
        point_collection: PointCollection,
        goal_placement_point: tuple,
        obj_type: AOE2ObjectType = None,
        margin: int = 0,
    ) -> CheckPlacementReturnTypes:
        """
        Checks if the given point is a valid placement for an object.

        Args:
            map_layer_type (MapLayerType): The map type.
            point_collection (PointCollection): The point manager.
            goal_placement_point (tuple): The point to place the object.
            obj_type (object, optional): The type of object to be placed. Defaults to None.
            margin (int, optional): The margin around the object. Defaults to 0.
            width (int, optional): The width of the object. Defaults to -1.
            height (int, optional): The height of the object. Defaults to -1.
        """
        x_range = ObjectInfo.get_object_rows(obj_type)
        height = ObjectInfo.get_object_columns(obj_type)
        eff_width = ObjectInfo.get_object_effective_size(obj_type, margin)
        eff_height = ObjectInfo.get_object_effective_size(obj_type, margin)

        x, y = goal_placement_point

        x_shift, y_shift = x_range // 2, height // 2
        # x_shift, y_shift = 0, 0

        for i in range(-margin, eff_width):
            for j in range(-margin, eff_height):
                if not point_collection.check_point_exists(
                    (x + i - x_shift, y + j - y_shift)
                ):
                    return CheckPlacementReturnTypes.FAIL

        return CheckPlacementReturnTypes.SUCCESS

    def __set_point_and_track_changes(
        self,
        point_collection: PointCollection,
        point: tuple[int, int],
        obj_type: AOE2ObjectType,
        map_layer_type: MapLayerType,
        player_id: PlayerId,
    ) -> None:
        """
        Safely sets a point on the map by removing it from the point manager and updating relevant static variables.
        """
        self.map.set_point(point, obj_type, map_layer_type, player_id)
        PlacerBase.points_set_on_map += 1
        point_collection.remove_point(point)
        PlacerBase.points_removed_from_point_collection += 1
        self.point_placement_record.add_object(point, MapObject(obj_type, player_id))

    # ---------------------------- SORTING FUNCTIONS ----------------------------

    def _default_clumping_func(self, p1, p2, clumping):
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
