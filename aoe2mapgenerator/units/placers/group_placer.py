"""
This file contains the GroupPlacerManager class which is used to place groups of objects on the map.
"""

import random
from typing import Callable

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType, CheckPlacementReturnTypes
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_PLAYER,
)
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType


class GroupPlacerManager(PlacerBase):
    """
    Class for placing groups of objects on a map.
    """

    points_iterated = 0

    # By default the object is placed in the first value from the map_layer_type list.
    def _place_group(
        self,
        map_layer_type: MapLayerType,
        point_manager: PointManager,
        obj_type: AOE2ObjectType,
        player_id: PlayerId = DEFAULT_PLAYER,
        group_size: int = 1,
        group_density: int = None,
        clumping: int = 1,
        clumping_func: Callable = None,
        margin: int = 0,
        start_point: tuple = None,
    ):
        """
        Places a single group of units on a specific array space.

        Args:
            map_layer_types (list[MapLayerType]): The list of map types.
            array_space_ids (list[Union[int, tuple]]): The list of array space ids to get points for.
            object_types (list, optional): The list of object types to be placed. Defaults to DEFAULT_OBJECT_TYPES.
            player_id (PlayerId, optional): The id of the object to be placed. Defaults to DEFAULT_PLAYER.
            group_size (int, optional): The number of members per group. Defaults to 1.
            group_density (int, optional): The percentage of available points to be used for the group. Defaults to None.
            clumping_factor (int, optional): How clumped the group members are. 0 is totally clumped. Higher numbers spread members out. Defaults to 1.
            clumping_func (Callable, optional): The function used to calculate the clumping score. Defaults to None.
            margin (int, optional): Margin between each object and any other object. Defaults to 0.
            start_point (tuple, optional): The starting point to place the group. Defaults to (-1,-1).
            ghost_margin (bool, optional): Whether to include ghost margins, i.e., change neighboring squares so nothing can use them. Defaults to True.
            place_on_n_maps (int, optional): Places group on the first n maps corresponding to the value types. Defaults to 1.
        """
        if player_id is None:
            player_id = DEFAULT_PLAYER

        if clumping_func is None:
            clumping_func = self._default_clumping_func

        points_list = point_manager.get_point_list()

        if len(points_list) == 0:
            return

        # Adjust group size based on density if specified
        if group_density is not None:
            group_size = group_density * len(points_list) // 100

        # Choose a random start point if none is specified or invalid
        if start_point is None:
            start_point = points_list[int(random.random() * len(points_list))]

        if clumping == -1:
            random.shuffle(points_list)
        else:
            total_size = sum(
                ObjectInfo.get_object_effective_size(obj_type, margin)
                for i in range(group_size)
            )
            # Gets points within three times the radius required for the group
            points_list = point_manager.get_nearby_points(
                start_point, (total_size ** (1 / 2)) * 2
            )

            # Sort the points based on clumping score if group size is in a certain range
            if 1 < group_size < len(points_list):
                points_list = sorted(
                    points_list,
                    key=lambda point: clumping_func(point, start_point, clumping),
                )

        # Try to place objects on the selected points
        placed = 0

        for x, y in points_list:
            GroupPlacerManager.points_iterated += 1
            if placed >= group_size:
                return

            status = self._check_placement(point_manager, (x, y), obj_type, margin)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return

            if status == CheckPlacementReturnTypes.SUCCESS:
                # Place the object on the first n maps
                self._place(
                    point_manager,
                    map_layer_type,
                    (x, y),
                    obj_type,
                    player_id,
                    margin,
                )

                placed += 1
        return

    def place_groups(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        player_id: PlayerId = DEFAULT_PLAYER,
        groups: int = 1,
        group_size: int = 1,
        group_density: int = None,
        groups_density: int = None,
        clumping: int = 0,
        clumping_func: Callable = None,
        margin: int = 0,
        start_point: tuple = None,
    ):
        """
        Places multiple groups of objects.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            obj_type: The type of object to be placed.
            player_id: Id of the object to be placed.
            margin: Margin between each object and any other object.
            group_size: Number of members per group.
            groups: Number of groups.
            clumping: How clumped the group members are. 0 is totally clumped. Higher numbers spread members out.
            ghost_margin: Option to include ghost margins, ie. change neighboring squares so nothing can use them.
        """

        if groups_density is not None:
            groups = groups_density * len(point_manager.get_point_list()) // 2000
            groups = int(groups)

        for i in range(groups):
            self._place_group(
                point_manager=point_manager,
                map_layer_type=map_layer_type,
                obj_type=obj_type,
                player_id=player_id,
                group_size=group_size,
                group_density=group_density,
                clumping=clumping,
                clumping_func=clumping_func,
                margin=margin,
                start_point=start_point,
            )

    # ---------------------------- HELPER METHODS ----------------------------------

    def _distance_to_edge(self, points, point):
        """
        Finds distance to edge blocks.

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
        """
        x, y = point

        for dist in range(1, 100):
            for i in range(-dist, dist + 1):
                for j in range(-dist, dist + 1):
                    if not (x + i, y + j) in points:
                        return dist

        return 100
