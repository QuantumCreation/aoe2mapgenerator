"""
TODO: Add description.
"""

import random


from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import (
    MapLayerType,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.units.placers.point_management.point_collection import (
    PointCollection,
)
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.common.types import AOE2ObjectType
from typing import List
from aoe2mapgenerator.units.utils import manhattan_distance
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.common.types import Point
from aoe2mapgenerator.units.placers.point_management.points_returned import PointPlacementResults
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceIfPossibleConfig,
    PlaceMultipleConfig,
    FillConfig,
)


class PlacerBase:
    """
    Base class for placing objects on a map.
    """

    points_removed_from_point_collection = 0
    points_set_on_map = 0

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map
        self.point_placement_record = PointPlacementResults()

    def place_closest_to_point(self, config: PlaceClosestToPointConfig) -> None:
        points: List[Point] = config.point_collection.get_point_list()
        search_radius = 5

        points = config.point_collection.get_nearby_points(config.starting_point, search_radius)

        for x, y in sorted(
            points,
            key=lambda point: manhattan_distance(point, config.starting_point),
        ):
            status = self._check_placement(config.point_collection, (x, y), config.obj_type, config.margin)
            if status == CheckPlacementReturnTypes.FAIL:
                continue

            self._place_single(
                config.point_collection,
                config.map_layer_type,
                (x, y),
                config.obj_type,
                config.player_id,
                config.margin,
            )
            return

    def place_if_possible(self, config: PlaceIfPossibleConfig) -> None:
        status = self._check_placement(
            config.point_collection, config.starting_point, config.obj_type, config.margin
        )

        if status == CheckPlacementReturnTypes.SUCCESS:
            self._place_single(
                config.point_collection,
                config.map_layer_type,
                config.starting_point,
                config.obj_type,
                config.player_id,
                config.margin,
            )
            return

    def place_multiple(self, config: PlaceMultipleConfig) -> None:
        for point in config.points:
            self._place_single(
                config.point_collection, config.map_layer_type, point, config.obj_type, config.player_id, config.margin
            )
        return

    def fill(self, config: FillConfig) -> None:
        for point in config.point_collection.get_point_list_copy():
            status = self._check_placement(config.point_collection, point, config.obj_type, config.margin)
            if status == CheckPlacementReturnTypes.SUCCESS:
                self._place_single(
                    config.point_collection, config.map_layer_type, point, config.obj_type, config.player_id, config.margin
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
        Directly sets a point on the map and tracks changes as necessary.

        Args:
            point_collection: The point manager.
            point: Point to place base of object.
            obj_type: The type of object to be placed.
            map_layer_type: The map type.
            player_id: Id of the player for the given object.
        """
        # Set the point on the map
        self.map.set_point(point, obj_type, map_layer_type, player_id)
        point_collection.remove_point(point)
        
        # Add the object to the point placement record
        self.point_placement_record.add_object(point, MapObject(obj_type, player_id))

        # Update the point collection
        PlacerBase.points_set_on_map += 1
        PlacerBase.points_removed_from_point_collection += 1

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
