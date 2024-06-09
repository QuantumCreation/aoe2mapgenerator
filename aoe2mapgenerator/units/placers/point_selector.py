"""
Docsting
"""

import functools

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.placer_configs import PointSelectorConfig


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
