"""
Handles all map generation and manipulation.
"""

from typing import Union, Callable, List, Tuple, Optional, Dict, Set, Any
from src.common.types import AOE2ObjectType, Point

from src.map.map import Map
from src.map.imap_manager import IMapManager
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from src.common.enums.enum import (
    MapLayerType,
    ObjectSize,
    GateType,
    TemplateTypes,
    ObjectRotation,
    YamlReplacementKeywords,
    CheckPlacementReturnTypes,
)

# Template imports
# from src.templates.template_decorator import get_template_manager
# from src.templates.template_types import TemplateType
# from src.templates.templates_manager import TemplateConfig

from src.scenario.scenario import Scenario
import numpy as np
import random
from src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    BASE_SCENE_DIR_LINUX,
    BASE_SCENARIO_NAME,
    TEMPLATE_DIR_LINUX,
    TEMPLATE_DIR_WINDOWS_WSL
)
from src.common.constants.default_objects import (
    GHOST_OBJECT_DISPLACEMENT,
)
import multiprocessing as mp
import os
from src.triggers.triggers import TriggerManager
import inspect
import ast
import ujson as json
from enum import Enum
from src.units.wallgenerators.voronoi import VoronoiGenerator
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from src.units.placers.statictemplate import TemplateCreator
from src.units.placers.group_placer import GroupPlacer
from src.units.placers.point_management.point_manager import (
    PointCollection,
)
from src.map.map_object import MapObject
from src.units.placers.point_management.point_selector import (
    PointSelector,
)
from src.visualizer.visualizer import Visualizer
from src.units.placers.gate_placer import GatePlacer
from src.units.placers.wall_placer import WallPlacer
from src.units.placers.placer_base import PlacerBase
from src.units.placers.point_management.point_manager import (
    PointCollection,
)
from src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
    DEFAULT_PLAYER,
    BASE_SCENE_DIR_WINDOWS_WSL
)
from src.units.placers.object_info import ObjectInfo
from src.units.placers.placer_configs import (
    PlaceGroupsConfig,
    AddBordersConfig,
    VoronoiGeneratorConfig,
    VisualizeMapConfig,
    PointSelectorConfig,
)
from src.units.placers.point_management.point_manager import (
    PointManager,
)
from src.scenario.scenario import Scenario

class MapManager(IMapManager):
    """
    Class to manage the map and its layers.
    """

    def __init__(self, map_size: int, output_dir: str = BASE_SCENE_DIR_WINDOWS_WSL) -> None:
        self.map: Map = Map(map_size)
        self.templates: list = []
        self.output_dir: str = output_dir
        self.scenario: Scenario = Scenario(self.map, os.path.join(self.output_dir, BASE_SCENARIO_NAME))

        # Initialize the placers - Legacy
        self.base_placer: PlacerBase = PlacerBase(self.map)
        self.wall_placer: WallPlacer = WallPlacer(self.map)
        self.gate_placer: GatePlacer = GatePlacer(self.map)
        self.group_placer: GroupPlacer = GroupPlacer(self.map)

        # Initialize the voronoi generator
        self.voronoi_generator: VoronoiGenerator = VoronoiGenerator(self.map)

        # Initialize the point selector and manager
        self.point_manager: PointManager = PointManager(self.map)

        # Initialize the visualizer
        self.visualizer: Visualizer = Visualizer(self.map)
        
        # Get the template manager with pre-registered templates
        # self.template_manager = get_template_manager()

    def write_map_and_save(self, file_name: str) -> 'MapManager':
        """
        Writes the map and saves it to a file.
        
        Args:
            file_name: The name of the file to save (without path)
            
        Returns:
            MapManager: Self for method chaining.
        """
        if self.scenario is None:
            self.scenario = Scenario(self.map)

        self.scenario._change_map_size(self.map.size)
        self.scenario.write_map()
        
        # Combine output directory with file name
        full_path = os.path.join(self.output_dir, file_name)
        self.scenario.save_file(full_path)
        return self

    def place_groups(
        self,
        configuration: PlaceGroupsConfig,
    ) -> 'MapManager':
        """
        Places groups of objects on the map.
        
        Returns:
            MapManager: Self for method chaining.
        """
        self.group_placer.place_groups(configuration)
        return self

    def place_borders(
        self,
        configuration: AddBordersConfig,
    ) -> 'MapManager':
        """
        Adds borders to the map.
        
        Returns:
            MapManager: Self for method chaining.
        """
        self.wall_placer.add_borders(configuration)
        return self

    def place_voronoi_zones(
        self,
        configuration: VoronoiGeneratorConfig,
    ) -> List[MapObject]:
        """
        Generates the voronoi zones.
        
        Returns:
            MapManager: Self for method chaining.
        """
        map_objects: List[MapObject] = self.voronoi_generator.generate_voronoi_cells(configuration)
        return map_objects

    def visualize_map(self, configuration: VisualizeMapConfig) -> 'MapManager':
        """
        Visualizes the map.
        
        Returns:
            MapManager: Self for method chaining.
        """
        self.visualizer.visualize_mat(configuration)
        return self

    def select_points(
        self, configuration: PointSelectorConfig
    ) -> list[tuple[int, int]]:
        """
        Selects points on the map.
        Note: This method doesn't support chaining as it returns the selected points.
        """
        return self.point_manager.point_selector.get_points_from_map_layer(
            configuration
        )

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
        return self.point_manager.point_selector.get_points_from_map_layer(
            configuration
        )

    def points(self) -> PointManager:
        """
        Access the point manager to work with point collections.
        This provides a cleaner interface for chaining point operations.
        
        Returns:
            PointManager: The point manager instance
        """
        return self.point_manager

    # def apply_template(
    #     self,
    #     template_type: TemplateType,
    #     point_collection: Optional[PointCollection] = None,
    #     config: Optional[TemplateConfig] = None,
    #     **kwargs
    # ) -> 'MapManager':
    #     """
    #     Apply a template to the map.
        
    #     Args:
    #         template_type: Enum value of the template to apply
    #         point_collection: Collection of points (creates new if None)
    #         config: Optional configuration 
    #         **kwargs: Additional parameters
            
    #     Returns:
    #         MapManager: Self for method chaining
    #     """
    #     if point_collection is None:
    #         point_collection = self.point_manager.create_point_collection(f"template_{template_type.name}")
        
    #     self.template_manager.apply_template(template_type, self, point_collection, config, **kwargs)
    #     return self
    
    # Convenience methods for common templates
    # def create_fort(
    #     self,
    #     center_point: Tuple[int, int] = (50, 50),
    #     size: int = 20,
    #     player_id: PlayerId = PlayerId.ONE,
    #     gate_type: GateType = GateType.FORTIFIED_GATE,
    #     **kwargs
    # ) -> 'MapManager':
    #     """
    #     Create a fort on the map.
        
    #     Args:
    #         center_point: Center coordinates of the fort
    #         size: Size of the fort
    #         player_id: Player who owns the fort
    #         gate_type: Type of gates to use
    #         **kwargs: Additional parameters for the template
            
    #     Returns:
    #         MapManager: Self for method chaining
    #     """
    #     config = TemplateConfig(
    #         center_point=center_point,
    #         size=size,
    #         player_id=player_id,
    #         gate_type=gate_type
    #     )
    #     return self.apply_template(TemplateType.FORT, config=config, **kwargs)
