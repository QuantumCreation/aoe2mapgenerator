"""
This file contains the GroupPlacerManager class which is used to place groups of objects on the map.
"""

import random
from typing import Callable

from AoE2ScenarioParser.datasets.players import PlayerId
from typing import List
from aoe2mapgenerator.src.common.enums.enum import (
    MapLayerType,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from aoe2mapgenerator.src.common.constants.constants import (
    DEFAULT_PLAYER,
)
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.src.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.src.common.types import AOE2ObjectType
from aoe2mapgenerator.src.units.placers.placer_configs import PlaceGroupsConfig


class GroupPlacerManager(PlacerBase):
    """
    Class for placing groups of objects on a map.
    """

    points_iterated = 0

    # By default the object is placed in the first value from the map_layer_type list.
    def _place_group(
        self,
        configuration: PlaceGroupsConfig,
    ):
        """
        Places a single group of units on a specific array space.

        Args:
            configuration (PlaceGroupsConfig): CoListnfiguration for placing a group of objects.
        """
        map_layer_type = configuration.map_layer_type
        point_manager = configuration.point_manager
        obj_type = configuration.object_type
        player_id = configuration.player_id
        group_size = configuration.group_size
        group_density = configuration.group_density
        clumping = configuration.clumping
        clumping_func = configuration.clumping_func
        margin = configuration.margin
        start_point = configuration.start_point

        if player_id is None:
            player_id = DEFAULT_PLAYER

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
            # Gets points within two times the radius required for the group
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
        all_placements: dict[str, List[tuple[int, int]]] = {
            "group_center": [start_point],
            "objects": [],
            "displacements": [],
        }

        for x, y in points_list:
            GroupPlacerManager.points_iterated += 1
            if placed >= group_size:
                break

            status = self._check_placement(point_manager, (x, y), obj_type, margin)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                break

            if status == CheckPlacementReturnTypes.SUCCESS:
                # Place the object on the first n maps
                placements = self.place_single(
                    point_manager,
                    map_layer_type,
                    (x, y),
                    obj_type,
                    player_id,
                    margin,
                )
                all_placements["objects"].extend(placements["objects"])
                all_placements["displacements"].extend(placements["displacements"])

                placed += 1

        return all_placements

    def place_groups(
        self,
        configuration: PlaceGroupsConfig,
    ) -> dict[str, List[tuple[int, int]]]:
        """
        Places multiple groups of objects.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing groups of objects.
        """
        point_manager = configuration.point_manager
        groups_density = configuration.groups_density
        groups = configuration.groups

        all_placements: dict[str, List[tuple[int, int]]] = {
            "group_centers": [],
            "objects": [],
            "displacements": [],
        }

        if groups_density is not None:
            # Scale off of object size
            size = ObjectInfo.get_object_size(configuration.object_type)
            groups = int(groups_density * len(point_manager.get_point_list()) // size)
            configuration.groups = int(groups)

        for i in range(groups):
            placements = self._place_group(
                configuration=configuration,
            )
            if placements is not None:
                all_placements["group_centers"].extend(placements["group_center"])
                all_placements["objects"].extend(placements["objects"])
                all_placements["displacements"].extend(placements["displacements"])

        return all_placements

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
