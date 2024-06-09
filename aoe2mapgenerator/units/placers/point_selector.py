"""
Docsting
"""

import functools

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.map.map_manager import MapManager


class PointSelector:
    """
    Class for selecting a set of points from the map.
    """

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map
        self.map_manager = MapManager(aoe2_map)

    def get_points_from_map_layer(
        self, map_layer_type: MapLayerType, object_type: MapObject
    ) -> list[tuple[int, int]]:
        """
        Gets the points from a map layer.

        Args:
            map_layer_type (MapLayerType): Type of map layer to use.
            object_type (MapObject): Type of object to use.
        """
        return list(self.map.get_set_with_map_object(map_layer_type, object_type))

    def get_intersection_of_spaces(
        self,
        map_layer_type_list: list[MapLayerType],
        obj_type_list: list[MapObject],
    ) -> list:
        """
        Gets the intersection of the different spaces.

        This method takes in a list of map layer types and a list of array space types,
        and returns a list of points that are in the intersection of the spaces.

        Args:
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns:
            list: List of points that are in the intersection of the spaces.
        """

        sets = []

        for map_layer_type, obj_type in zip(map_layer_type_list, obj_type_list):

            dictionary = self.map.get_dictionary_from_map_layer_type(map_layer_type)

            # If the space type is None, then it is ignored for the purpose of the intersection.
            # This means that if we only have None as the array_space_type, then the intersection will be empty.
            # However, if one of the other array_space_types is not None, then the intersection will be the intersection of all the non-None types.
            if obj_type is None:
                continue

            if isinstance(obj_type, list):
                obj_type = tuple(obj_type)

            if obj_type not in dictionary:
                raise ValueError(
                    f"Array space type {obj_type} is not valid for map layer {map_layer_type}."
                )

            s = dictionary[obj_type]

            sets.append(s)

        return functools.reduce(lambda a, b: a & b, sets)

    def get_union_of_spaces(
        self, map_layer_type_list: list[MapLayerType], obj_type_list: list[MapObject]
    ) -> list:
        """
        Gets the union of the different spaces.

        Args:
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns:
            list: List of points that are in the union of the spaces.
        """

        sets = []

        for map_layer_type, array_space_type in zip(map_layer_type_list, obj_type_list):
            dictionary = self.map.get_dictionary_from_map_layer_type(map_layer_type)

            # If the space type is None, then it is ignored for the purpose of the union.
            # This means that if we only have None as the array_Space_type, then the union will be empty.
            # However, if one of the other array_space_types is not None, then the union will be the union of all the non-None types.
            if array_space_type is None:
                continue

            if isinstance(array_space_type, list):
                array_space_type = tuple(array_space_type)

            if array_space_type not in dictionary:
                raise ValueError(
                    f"Array space type {array_space_type} is not valid for map layer {map_layer_type}."
                )

            s = dictionary[array_space_type]

            sets.append(s)

        return functools.reduce(lambda a, b: a | b, sets)
