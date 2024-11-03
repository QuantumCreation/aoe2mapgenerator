"""
Docsting
"""

import functools
from typing import List
from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.units.placers.placer_configs import (
    PointSelectorConfig,
    PointSelectorInRangeConfig,
)
from aoe2mapgenerator.src.units.utils import manhattan_distance
from aoe2mapgenerator.src.units.placers.point_manager import PointManager


class PointSelector:
    """
    Class for selecting a set of points from the map.
    """

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map

    def get_points_from_map_layer(
        self,
        configuration: PointSelectorConfig,
    ) -> list[tuple[int, int]]:
        """
        Gets the points from a map layer.

        Args:
            map_layer_type (MapLayerType): Type of map layer to use.
            object_type (MapObject): Type of object to use.
        """
        map_layer_type = configuration.map_layer_type
        object_type = configuration.object_type
        return list(self.map.get_set_with_map_object(map_layer_type, object_type))

    def get_points_in_range(
        self, configuration: PointSelectorInRangeConfig
    ) -> list[tuple[int, int]]:
        """
        Gets the points from a map layer.

        Args:
            map_layer_type (MapLayerType): Type of map layer to use.
            object_type (MapObject): Type of object to use.
            min_range (int): Minimum range to select points from.
            max_range (int): Maximum range to select points from.
            points_to_be_in_range_of (list[tuple[int, int]]): Points to be in range of.
        """
        map_layer_type = configuration.map_layer_type
        object_type = configuration.object_type
        min_range = configuration.min_range
        max_range = configuration.max_range
        points_to_be_in_range_of = configuration.points_to_be_in_range_of

        points = set()
        for point in points_to_be_in_range_of:
            points.update(
                self.get_points_in_range_of_point(
                    point,
                    map_layer_type,
                    object_type,
                    min_range,
                    max_range,
                )
            )

        return list(points)

    def get_points_in_range_of_point(
        self,
        point: tuple[int, int],
        map_layer_type: MapLayerType,
        object_type: MapObject,
        min_range: int,
        max_range: int,
    ) -> set[tuple[int, int]]:
        """
        Gets the points from a map layer.

        Args:
            point (tuple[int, int]): Point to be in range of.
            map_layer_type (MapLayerType): Type of map layer to use.
            object_type (MapObject): Type of object to use.
            min_range (int): Minimum range to select points from.
            max_range (int): Maximum range to select points from.
        """
        points = self.get_points_from_map_layer(
            PointSelectorConfig(map_layer_type, object_type)
        )

        return {
            potential_point
            for potential_point in points
            if min_range <= manhattan_distance(potential_point, point) <= max_range
        }

    # def get_all_points_in_range(
    #     self, point: tuple[int, int], point_manager: PointManager
    # ) -> List[tuple[int, int]]:
    #     """
    #     Gets all points in range of a point.
    #     """
    #     potential_points =
