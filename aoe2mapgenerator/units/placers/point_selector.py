
import random
from re import A
from site import abs_paths
from telnetlib import GA
from typing import Union, Callable

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
import functools

from aoe2mapgenerator.common.enums.enum import ObjectSize, Directions, MapLayerType, GateTypes, CheckPlacementReturnTypes
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from aoe2mapgenerator.map.map import Map




class PointSelector():

    def __init__(self, map: Map):
        self.map = map

    def get_intersection_of_spaces(self, map_layer_type_list: list[MapLayerType], array_space_type_list: list) -> list:
        """
        Gets the union of the different spaces.

        Args:
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns: 
            list: List of points that are in the intersection of the spaces.
        """

        sets = []

        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
            
            dictionary = self.map.get_dictionary_from_map_layer_type(map_layer_type)

            # If the space type is None, then it is ignored for the purpose of the union.
            # This means that if we only have None as the array_Space_type, then the union will be empty.
            # However, if one of the other array_space_types is not None, then the union will be the union of all the non-None types.
            if array_space_type is None:
                continue
            
            if type(array_space_type) == list:
                array_space_type = tuple(array_space_type)
            
            if array_space_type not in dictionary:
                raise ValueError(f"Array space type {array_space_type} is not valid for map layer {map_layer_type}.")
            
            s = dictionary[array_space_type]
            
            sets.append(s)

        return functools.reduce(lambda a, b: a & b, sets)

    def get_union_of_spaces(self, map_layer_type_list: list[MapLayerType], array_space_type_list: list) -> list:
        """
        Gets the union of the different spaces.

        Args:
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns: 
            list: List of points that are in the union of the spaces.
        """

        sets = []

        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
            
            dictionary = self.map.get_dictionary_from_map_layer_type(map_layer_type)

            # If the space type is None, then it is ignored for the purpose of the union.
            # This means that if we only have None as the array_Space_type, then the union will be empty.
            # However, if one of the other array_space_types is not None, then the union will be the union of all the non-None types.
            if array_space_type is None:
                continue
            
            if type(array_space_type) == list:
                array_space_type = tuple(array_space_type)
            
            if array_space_type not in dictionary:
                raise ValueError(f"Array space type {array_space_type} is not valid for map layer {map_layer_type}.")
            
            s = dictionary[array_space_type]
            
            sets.append(s)

        return functools.reduce(lambda a, b: a | b, sets)