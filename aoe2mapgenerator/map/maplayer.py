from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable
import numpy as np

from aoe2mapgenerator.common.constants.constants import DEFAULT_EMPTY_VALUE, DEFAULT_OBJECT_AND_PLAYER
from aoe2mapgenerator.units.wallgenerators.voronoi import VoronoiGeneratorMixin
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.objectplacer import PlacerMixin
from aoe2mapgenerator.units.placers.templateplacer import TemplatePlacerMixin
from aoe2mapgenerator.map.map_utils import MapUtilsMixin
from aoe2mapgenerator.visualizer.visualizer import VisualizerMixin


class MapLayer():
    """
    Single Map type constructor.
    """

    def __init__(self, map_layer_type: MapLayerType, size: int = 100, array = [], dictionary = {}):
        
        self.layer = map_layer_type
        self.size = size
        self.array = []
        self.dict = {}

        if array == []:
            self.array = [[(DEFAULT_EMPTY_VALUE, PlayerId.GAIA) for i in range(size)] for j in range(size)]
        else:
            self.array = array
        
        if dictionary == {}:
            self.dict = _create_dict(self.array)
        else:
            self.dict = dictionary
        
    
    def set_point(self, x, y, new_value, player_id : PlayerId = PlayerId.GAIA):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        # Retrieve correct dictionary and array.
        d = self.dict
        a = self.array
        
        try:
             # Remove element from the dictionary.
            d[a[x][y]].remove((x,y))
        except:
            pass

        # Remove entire dictionary entry if there are not elements left.
        if len(d[a[x][y]]) == 0:
            d.pop(a[x][y], None)

        # Assign new value to the array.
        a[x][y] = (new_value, player_id)

        # Add the value to the dictionary.
        if (new_value, player_id) in d:
            d[a[x][y]].add((x,y))
        else:
            d[a[x][y]] = {(x,y)}
    
    def get_array(self):
        return self.array
    
    def get_dict(self):
        return self.dict

def _create_dict(array: list[list[object]]):
    """
    Creates a set representation from the array.
    """

    new_dict = dict()

    for i in range(len(array)):
        for j in range(len(array[0])):
            if array[i][j] in new_dict:
                new_dict[array[i][j]].add((i,j))
            else:
                new_dict[array[i][j]] = {(i,j)}
    
    return new_dict
