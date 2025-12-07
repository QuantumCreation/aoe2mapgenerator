"""
This file contains the GroupPlacerManager class which is used to place groups of objects on the map.
"""

import random
from typing import Callable

from AoE2ScenarioParser.datasets.players import PlayerId
from typing import List
from aoe2mapgenerator.common.enums.enum import (
    MapLayerType,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_PLAYER,
)
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
from aoe2mapgenerator.common.types import Point
from aoe2mapgenerator.units.placers.point_management.points_returned import PointPlacementResults


class GroupPlacer(PlacerBase):
    """
    Class for placing groups of objects on a map.
    """

    points_iterated = 0

    def place_groups(
        self,
        configuration: PlaceGroupsConfig,
    ) -> None:
        """
        Places multiple groups of objects.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing groups of objects.

        Returns:
            dict[str, List[tuple[int, int]]]: Dictionary containing group centers, objects, and displacements.
        """
        groups = self._determine_group_count(configuration)

        for _ in range(groups):
            self._place_group(configuration)

    def _place_group(
        self,
        configuration: PlaceGroupsConfig,
    ) -> None:
        """
        Places a single group of units on a specific array space.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing a group of objects.

        Returns:
            dict[str, List[tuple[int, int]]] | None: Dictionary containing group center, objects, and displacements or None if no points are available.
        """
        player_id = configuration.player_id or DEFAULT_PLAYER
        points_list = configuration.point_collection.get_point_list()

        if not points_list:
            return None

        group_size: int = self._adjust_group_size(configuration, points_list)
        start_point: Point = self._choose_start_point(configuration, points_list)
        points_list = self._prepare_points_list(configuration, points_list, start_point)

        self._place_objects(configuration, points_list, group_size, player_id)


    def _determine_group_count(self, configuration: PlaceGroupsConfig) -> int:
        """
        Determines the number of groups to place based on the configuration.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing groups of objects.

        Returns:
            int: Number of groups to place.
        """
        # Check if a density-based approach should be used for determining group count
        if configuration.groups_density is not None:
            # Get the size of each object to understand space requirements
            size = ObjectInfo.get_object_size(configuration.object_type)
            
            # Calculate number of groups based on:
            # - The specified density (as a percentage or multiplier)
            # - Total available points in the collection
            # - Divided by the object size to account for space needed per object
            groups = int(
            configuration.groups_density
            * len(configuration.point_collection.get_point_list())
            // size
            )
            
            # Update the configuration with the calculated group count
            return groups
            
        # Return the final group count from the configuration
        return configuration.groups

    def _adjust_group_size(
        self, configuration: PlaceGroupsConfig, points_list: List[tuple[int, int]]
    ) -> int:
        """
        Adjusts the group size based on the configuration and points list.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing a group of objects.
            points_list (List[tuple[int, int]]): List of points available for placement.

        Returns:
            int: Adjusted group size.
        """
        if configuration.group_density is not None:
            size = ObjectInfo.get_object_size(configuration.object_type)

            group_size = int(
                configuration.group_density
                * len(points_list)
                // size
            )

            return group_size
        return configuration.group_size

    def _choose_start_point(
        self, configuration: PlaceGroupsConfig, points_list: List[tuple[int, int]]
    ) -> tuple[int, int]:
        """
        Chooses a start point for placing the group.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing a group of objects.
            points_list (List[tuple[int, int]]): List of points available for placement.

        Returns:
            tuple[int, int]: Chosen start point.
        """
        if configuration.start_point is None:
            return points_list[int(random.random() * len(points_list))]
        return configuration.start_point

    def _prepare_points_list(
        self,
        configuration: PlaceGroupsConfig,
        points_list: List[Point],
        start_point: Point,
    ) -> List[Point]:
        """
        Prepares the points list based on the configuration and start point. This finds the points closest to the start point
        and sorts them based on the clumping function.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing a group of objects.
            points_list (List[tuple[int, int]]): List of points available for placement.
            start_point (tuple[int, int]): Chosen start point.

        Returns:
            List[tuple[int, int]]: Prepared points list.
        """
        if configuration.clumping == -1:
            random.shuffle(points_list)
        else:
            total_size = sum(
                ObjectInfo.get_object_effective_size(
                    configuration.object_type, configuration.margin
                )
                for _ in range(configuration.group_size)
            )
            points_list = configuration.point_collection.get_nearby_points(
                start_point, (total_size**0.5) * 2
            )
            if 1 < configuration.group_size < len(points_list):
                points_list = sorted(
                    points_list,
                    key=lambda point: configuration.clumping_func(
                        point, start_point, configuration.clumping
                    ),
                )
        return points_list

    def _place_objects(
        self,
        configuration: PlaceGroupsConfig,
        points_list: List[tuple[int, int]],
        group_size: int,
        player_id: PlayerId,
    ) -> None:
        """
        Places objects on the map based on the configuration and points list.

        Args:
            configuration (PlaceGroupsConfig): Configuration for placing a group of objects.
            points_list (List[tuple[int, int]]): List of points available for placement.
            start_point (tuple[int, int]): Chosen start point.
            group_size (int): Size of the group to be placed.
            player_id (PlayerId): ID of the player placing the objects.

        Returns:
            dict[str, List[tuple[int, int]]]: Dictionary containing group center, objects, and displacements.
        """
        placed = 0

        for x, y in points_list:
            GroupPlacer.points_iterated += 1
            if placed >= group_size:
                break

            status = self._check_placement(
                configuration.point_collection,
                (x, y),
                configuration.object_type,
                configuration.margin,
            )

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                break

            if status == CheckPlacementReturnTypes.SUCCESS:
                self._place_single(
                    configuration.point_collection,
                    configuration.map_layer_type,
                    (x, y),
                    configuration.object_type,
                    player_id,
                    configuration.margin,
                )
                placed += 1

    # ---------------------------- HELPER METHODS ----------------------------------

    def __distance_to_edge(self, points, point):
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
