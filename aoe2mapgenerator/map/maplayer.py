from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable, List
import numpy as np

from aoe2mapgenerator.common.constants.constants import DEFAULT_EMPTY_VALUE, DEFAULT_OBJECT_AND_PLAYER
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.objectplacer import PlacerMixin
from aoe2mapgenerator.units.placers.templateplacer import TemplatePlacerMixin
from aoe2mapgenerator.map.map_utils import MapUtilsMixin
from aoe2mapgenerator.visualizer.visualizer import VisualizerMixin
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from dataclasses import dataclass
from aoe2mapgenerator.map.map_object import MapObject

MapLayerArray = List[List[MapObject]]
MapLayerDictionary = dict[MapObject, set[tuple[int, int]]]

class MapLayer():
    """
    Single Map type constructor.
    """

    def __init__(self, map_layer_type: MapLayerType, size: int = 100, array: MapLayerArray = [], dict: MapLayerDictionary = {}) -> None:
        
        self.layer = map_layer_type
        self.size = size
        self.array = []
        self.dict = {}

        if array == []:
            self.array = [[(DEFAULT_EMPTY_VALUE, PlayerId.GAIA) for i in range(size)] for j in range(size)]
        else:
            self.array = array
        
        if dict == {}:
            self.dict = _create_dict(self.array)
        else:
            self.dict = dict
        
    
    def set_point(self, x: int, y: int, new_value: AOE2ObjectType, player_id : PlayerId = PlayerId.GAIA) -> None:
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        # Retrieve correct dictionary and array.
        dictionary = self.dict
        array = self.array
        
        # Remove element from the dictionary.
        dictionary[array[x][y]].remove((x,y))

        # Remove entire dictionary entry if there are not elements left.
        if len(dictionary[array[x][y]]) == 0:
            dictionary.pop(array[x][y], None)

        new_obj = MapObject(new_value, player_id)
        
        # Assign new value to the array.
        array[x][y] = new_obj

        # Add the value to the dictionary.
        if array[x][y] in dictionary:
            dictionary[array[x][y]].add((x,y))
        else:
            dictionary[array[x][y]] = {(x,y)}
    
    def get_array(self):
        return self.array
    
    def get_dict(self):
        return self.dict

def _create_dict(array: list[list[object]]) -> MapLayerDictionary:
    """
    Creates a set representation from the array.
    """

    new_dict: MapLayerDictionary = dict()

    for i in range(len(array)):
        for j in range(len(array[0])):
            if array[i][j] in new_dict:
                new_dict[array[i][j]].add((i,j))
            else:
                new_dict[array[i][j]] = {(i,j)}
    
    return new_dict
