from dataclasses import dataclass
import random
from re import A
from site import abs_paths
from aoe2mapgenerator.common.constants.constants import DEFAULT_OBJECT_TYPES, DEFAULT_PLAYER
from aoe2mapgenerator.common.constants.default_objects import GHOST_OBJECT_DISPLACEMENT, GHOST_OBJECT_MARGIN
from aoe2mapgenerator.utils.utils import set_from_matrix
from aoe2mapgenerator.common.enums.enum import ObjectSize, MapLayerType, GateTypes
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.units.placers.objectplacer import PlacerMixin
from aoe2mapgenerator.common.constants.constants import TEMPLATE_DIR, DEFAULT_PLAYER
import re
from typing import Union
from yaml import load, UnsafeLoader
import os
from aoe2mapgenerator.common.enums.enum import YamlReplacementKeywords
from time import time
from copy import deepcopy
import inspect
from difflib import SequenceMatcher
import ast
from aoe2mapgenerator.map.map import Map

class TemplateCreator():
    """
    Class to create a template from a map
    """

    def __init__(self):
        self.map = self.create_map()
    
    def create_map(self, map_size: int = 50) -> Map:
        """
        Create the map from the template
        """
        self.map = Map(map_size)
        return self.map

    def fill_template(self, template: str) -> None:
        """
        Place the template on the map
        """
        self.map.place_template(
            'oak_forest.yaml',
            map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
            array_space_type_list = [zone, (TerrainId.GRASS_2, PlayerId.GAIA), zone, zone],
            player_id = PlayerId.ONE,
        )
    
    def overlay_template_map_onto_base_map(self, template_map: Map, base_map: Map, x_location: int, y_location: int) -> None:
        """
        Overlay the template map onto the base map

        Args:
            template_map (Map): The map to overlay
            base_map (Map): The map to overlay onto
            x_location (int): The x location to overlay the map
            y_location (int): The y location to overlay the map
        """

        all_map_layers = template_map.get_all_map_layers()

        for map_layer in all_map_layers:
            map_layer_array = map_layer.get_array()
            for i in range(len(map_layer_array)):
                for j in range(len(map_layer_array[i])):
                    base_map.set_point(i + x_location, j + y_location, map_layer_array[i][j][0], map_layer_array[i][j][1])