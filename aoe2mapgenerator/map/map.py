from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable
import numpy as np

from aoe2mapgenerator.common.constants.constants import DEFAULT_EMPTY_VALUE, DEFAULT_OBJECT_AND_PLAYER
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.objectplacer import PlacerMixin
from aoe2mapgenerator.units.placers.templateplacer import TemplatePlacerMixin
from aoe2mapgenerator.map.map_utils import MapUtilsMixin
from aoe2mapgenerator.visualizer.visualizer import VisualizerMixin
from aoe2mapgenerator.map.maplayer import MapLayer
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from aoe2mapgenerator.map.map_object import MapObject


class Map(TemplatePlacerMixin, VisualizerMixin, MapUtilsMixin):
    """
    Class for the Age of Empires Map layers
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

        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError("Map layer type is not a MapLayerType.")
        
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
    
    def get_all_map_layers(self) -> list[MapLayer]:
        """
        Gets all map layers.
        """
        return [self.unit_map_layer, self.zone_map_layer, self.terrain_map_layer, self.decor_map_layer, self.elevation_map_layer]

    def set_point(self, x: int, y: int, new_value: AOE2ObjectType, map_layer_type: MapLayerType, player_id : PlayerId = PlayerId.GAIA):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """        
        layer = self.get_map_layer(map_layer_type)
        layer.set_point(x, y, new_value, player_id)

    # THIS PROBOBLY BELONGS SOMEWHERE ELSE, Also handle defaults better somehow
    # def voronoi(self, 
    #             interpoint_distance: int = 25,
    #             map_layer_type_list: list = 
    #             [may_layer_type for may_layer_type in MapLayerType],
    #             array_space_type_list: list = 
    #             [DEFAULT_OBJECT_AND_PLAYER for i in range(5)]
    #             ) -> list:
    #     """
    #     Generates a voronoi cell map.

    #     Args:
    #         interpoint_distance (int): Minimum distance between points.
    #         map_layer_type_list (list): List of map layer types to use.
    #         array_space_type_list (list): List of array space types to use.
        
    #     Returns:
    #         list: List of unqiue values for each voronoi cell.
    #     """


    #     # Generate voronoi cells. Implicitly edits the map.
    #     voronoi_zones = self.generate_voronoi_cells(
    #                                 interpoint_distance,
    #                                 map_layer_type_list,
    #                                 array_space_type_list)

    #     return voronoi_zones       
