from common.constants.constants import DEFAULT_EMPTY_VALUE
from units.wallgenerators.voronoi import VoronoiGeneratorMixin
from common.enums.enum import MapLayerType
from units.placers.objectplacer import PlacerMixin
from units.placers.templateplacer import TemplatePlacerMixin
from map.map_utils import MapUtilsMixin
from visualizer.visualizer import VisualizerMixin
from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable

class Map(TemplatePlacerMixin, VisualizerMixin, VoronoiGeneratorMixin, MapUtilsMixin):
    """
    TODO
    """

    def __init__(self, size: int = 100):
        """
        Initializes map object for internal map representation.

        Args:
            size: Size of the map.
        """
        # TEMPLATE NAMES, MULTIPLE INHERITANCE, init, AAHGHG
        self.template_names = {}
        self.size = size
        self.unit_map_layer = MapLayer(MapLayerType.UNIT, self.size)
        self.zone_map_layer = MapLayer(MapLayerType.ZONE, self.size)
        self.terrain_map_layer = MapLayer(MapLayerType.TERRAIN, self.size)
        self.decor_map_layer = MapLayer(MapLayerType.DECOR, self.size)
        self.elevation_map_layer = MapLayer(MapLayerType.ELEVATION, self.size)
    
    def get_map_layer(self, map_layer_type: MapLayerType):
        """
        Gets the corresponding map layer from a map layer type.
        """
        if map_layer_type == MapLayerType.ZONE:
            return self.zone_map_layer
        elif map_layer_type == MapLayerType.TERRAIN:
            return self.terrain_map_layer
        elif map_layer_type == MapLayerType.UNIT:
            return self.unit_map_layer
        elif map_layer_type == MapLayerType.DECOR:
            return self.decor_map_layer
        elif map_layer_type == MapLayerType.ELEVATION:
            return self.elevation_map_layer
        
        raise ValueError("Retrieving map layer from map layer type failed.")

    def set_point(self, x, y, new_value, map_layer_type: Union[MapLayerType, int], player_id : PlayerId = PlayerId.GAIA):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        layer = self.get_map_layer(map_layer_type)
        layer.set_point(x, y, new_value, player_id)

    # THIS PROBOBLY BELONGS SOMEWHERE ELSE
    def voronoi(self, interpoint_distance):
        """
        Generates a voronoi cell map.
        """
        self.zone_map_layer.array = self.generate_voronoi_cells(self.size, interpoint_distance)
        self.zone_map_layer.dict = _create_dict(self.zone_map_layer.array)

        self.unit_map_layer.array = deepcopy(self.zone_map_layer.array)
        self.unit_map_layer.dict = _create_dict(self.unit_map_layer.array)

        self.terrain_map_layer.array = deepcopy(self.zone_map_layer.array)
        self.terrain_map_layer.dict = _create_dict(self.terrain_map_layer.array)

        self.decor_map_layer.array = deepcopy(self.zone_map_layer.array)
        self.decor_map_layer.dict = _create_dict(self.decor_map_layer.array)

class MapLayer():
    """
    Single Map type constructor.
    """

    def __init__(self, layer: MapLayerType, size: int = 100, array = [], dictionary = {}):
        
        self.layer = layer
        self.size = size

        if array == []:
            self.array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
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
        
        # Remove element from the dictionary.
        d[a[x][y]].remove((x,y))

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