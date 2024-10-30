"""
Handles all map generation and manipulation.
"""

from typing import Union

from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.map.map import Map
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.src.common.enums.enum import (
    MapLayerType,
    ObjectSize,
    GateType,
    TemplateTypes,
    ObjectRotation,
    YamlReplacementKeywords,
    CheckPlacementReturnTypes,
)

from aoe2mapgenerator.src.scenario.scenario import Scenario
import numpy as np
import random
from aoe2mapgenerator.src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    BASE_SCENE_DIR_LINUX,
    BASE_SCENARIO_NAME,
    TEMPLATE_DIR_LINUX,
)
from aoe2mapgenerator.src.common.constants.default_objects import (
    GHOST_OBJECT_DISPLACEMENT,
)
from aoe2mapgenerator.src.common.enums.enum import GateType
import multiprocessing as mp
from aoe2mapgenerator.src.map.map import Map
import os
from aoe2mapgenerator.src.serializer.serializer import (
    _convert_map_value_to_string,
    _get_enum_list,
    _recursive_parse_enum_to_string,
    serialize_map,
    get_all_functions_and_arguments,
    _get_functions,
    _get_function_arguments,
    _get_default_arguments,
    _convert_enum_instance_to_string,
)
from aoe2mapgenerator.src.triggers.triggers import TriggerObject
from aoe2mapgenerator.src.maingenerator import main_map_generator
import inspect
import ast
import json
from enum import Enum
from aoe2mapgenerator.src.units.wallgenerators.voronoi import VoronoiGenerator
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from aoe2mapgenerator.src.units.placers.statictemplate import TemplateCreator
from aoe2mapgenerator.src.units.placers.group_placer import GroupPlacerManager
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from aoe2mapgenerator.src.testing import awesome_function
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.units.placers.point_selector import PointSelector
from aoe2mapgenerator.src.visualizer.visualizer import Visualizer
from aoe2mapgenerator.src.units.placers.gate_placer import GatePlacer
from aoe2mapgenerator.src.units.placers.wall_placer import WallPlacer
from aoe2mapgenerator.src.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from aoe2mapgenerator.src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
    DEFAULT_PLAYER,
)
from typing import Callable
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.src.common.enums.enum import AOE2ObjectType
from aoe2mapgenerator.src.units.placers.placer_configs import (
    PlaceGroupsConfig,
    AddBordersConfig,
    VoronoiGeneratorConfig,
    VisualizeMapConfig,
    PointSelectorConfig,
)


class MapManager:
    """
    Class to manage the map and its layers.
    """

    def __init__(self, map_size: int):
        self.map = Map(map_size)
        self.templates: list = []

        # Initialize the placers
        self.base_placer = PlacerBase(self.map)
        self.wall_placer = WallPlacer(self.map)
        self.gate_placer = GatePlacer(self.map)
        self.group_placer = GroupPlacerManager(self.map)
        self.voronoi_generator = VoronoiGenerator(self.map)

        # Initialize the point selector and manager
        self.point_selector = PointSelector(self.map)
        self.point_manager = PointManager()

        # Initialize the visualizer
        self.visualizer = Visualizer(self.map)

    def get_new_point_manager(self) -> PointManager:
        """
        Returns a new point manager.
        """
        return PointManager()

    def place_groups(
        self,
        configuration: PlaceGroupsConfig,
    ) -> dict[str, list[tuple[int, int]]]:
        """
        Places groups of objects on the map.
        """
        return self.group_placer.place_groups(configuration)

    def place_borders(
        self,
        configuration: AddBordersConfig,
    ):
        """
        Adds borders to the map.
        """
        self.wall_placer.add_borders(configuration)

    def place_voronoi_zones(
        self,
        configuration: VoronoiGeneratorConfig,
    ) -> list[MapObject]:
        """
        Generates the voronoi zones.
        """
        return self.voronoi_generator.generate_voronoi_cells(configuration)

    def visualize_map(self, configuration: VisualizeMapConfig):
        """
        Visualizes the map.
        """
        self.visualizer.visualize_mat(configuration)

    def select_points(
        self, configuration: PointSelectorConfig
    ) -> list[tuple[int, int]]:
        """
        Selects points on the map.
        """
        return self.point_selector.get_points_from_map_layer(configuration)

    def get_map(self):
        """
        Returns the map object.
        """
        return self.map

    def get_map_layer(self, map_layer_type: MapLayerType):
        """
        Returns the map layer object.
        """
        return self.map.get_map_layer(map_layer_type)

    def get_dictionary(self, map_layer_type: MapLayerType) -> dict:
        """
        Returns the dictionary of the map layer.
        """
        return self.map.get_map_layer(map_layer_type).get_dict()

    def get_array(self, map_layer_type: MapLayerType) -> list:
        """
        Returns the array of the map layer.
        """
        return self.map.get_map_layer(map_layer_type).get_array()

    def get_set_with_map_object(self, map_layer_type: MapLayerType, obj: MapObject):
        """
        Returns the set of points with the object.
        """
        return self.map.get_map_layer(map_layer_type).get_set_with_map_object(obj)

    def get_points_from_map_layer(
        self,
        configuration: PointSelectorConfig,
    ) -> list[tuple[int, int]]:
        """
        Gets the points from a map layer.
        """
        return self.point_selector.get_points_from_map_layer(configuration)
