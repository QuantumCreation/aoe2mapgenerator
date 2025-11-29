"""
Handles all map generation and manipulation.
"""

from typing import Union, Callable, List, Tuple, Optional, Dict, Set, Any
from src.common.types import AOE2ObjectType, Point

from src.map.map import Map
from src.map.imap_manager import IMapManager
from AoE2ScenarioParser.datasets.players import PlayerId
from src.common.enums.enum import (
    MapLayerType,
    GateType,
)
# Template imports
from src.templates.template_decorator import get_template_manager
from src.templates.template_types import TemplateType
from src.templates.templates_manager import TemplateConfig

from src.scenario.scenario import Scenario
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
import os
from src.units.wallgenerators.voronoi import VoronoiGenerator
from src.units.placers.group_placer import GroupPlacer
from src.units.placers.point_management.point_manager import (
    PointCollection,
)
from src.map.map_object import MapObject
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
from src.templates.decor import OakForestTemplate

class MapManager(IMapManager):
    """
    Class to manage the map and its layers.
    """

    def __init__(self, map_size: int, output_dir: str = BASE_SCENE_DIR_WINDOWS_WSL) -> None:
        self._map: Map = Map(map_size)
        self._templates: list = []
        self._output_dir: str = output_dir
        self._scenario: Scenario = Scenario(self._map, os.path.join(self._output_dir, BASE_SCENARIO_NAME))

        # Initialize the placers - Legacy
        self._base_placer: PlacerBase = PlacerBase(self._map)
        self._wall_placer: WallPlacer = WallPlacer(self._map)
        self._gate_placer: GatePlacer = GatePlacer(self._map)
        self._group_placer: GroupPlacer = GroupPlacer(self._map)

        # Initialize the voronoi generator
        self._voronoi_generator: VoronoiGenerator = VoronoiGenerator(self._map)

        # Initialize the point selector and manager
        self._point_manager: PointManager = PointManager(self._map)

        # Initialize the visualizer
        self._visualizer: Visualizer = Visualizer(self._map)
        
        # Get the template manager with pre-registered templates
        self.template_manager = get_template_manager()

    # Property getters and setters for interface implementation
    @property
    def map(self) -> Map:
        """
        Returns the map object.
        """
        return self._map
        
    @map.setter
    def map(self, value: Map) -> None:
        """
        Sets the map object.
        """
        self._map = value

    @property
    def templates(self) -> list:
        """
        Returns the list of templates.
        """
        return self._templates
        
    @templates.setter
    def templates(self, value: list) -> None:
        """
        Sets the list of templates.
        """
        self._templates = value

    @property
    def output_dir(self) -> str:
        """
        Returns the output directory.
        """
        return self._output_dir
        
    @output_dir.setter
    def output_dir(self, value: str) -> None:
        """
        Sets the output directory.
        """
        self._output_dir = value

    @property
    def scenario(self) -> Scenario:
        """
        Returns the scenario.
        """
        return self._scenario
        
    @scenario.setter
    def scenario(self, value: Scenario) -> None:
        """
        Sets the scenario.
        """
        self._scenario = value

    @property
    def base_placer(self) -> PlacerBase:
        """
        Returns the base placer.
        """
        return self._base_placer
        
    @base_placer.setter
    def base_placer(self, value: PlacerBase) -> None:
        """
        Sets the base placer.
        """
        self._base_placer = value

    @property
    def wall_placer(self) -> WallPlacer:
        """
        Returns the wall placer.
        """
        return self._wall_placer
        
    @wall_placer.setter
    def wall_placer(self, value: WallPlacer) -> None:
        """
        Sets the wall placer.
        """
        self._wall_placer = value

    @property
    def gate_placer(self) -> GatePlacer:
        """
        Returns the gate placer.
        """
        return self._gate_placer
        
    @gate_placer.setter
    def gate_placer(self, value: GatePlacer) -> None:
        """
        Sets the gate placer.
        """
        self._gate_placer = value

    @property
    def group_placer(self) -> GroupPlacer:
        """
        Returns the group placer.
        """
        return self._group_placer
        
    @group_placer.setter
    def group_placer(self, value: GroupPlacer) -> None:
        """
        Sets the group placer.
        """
        self._group_placer = value

    @property
    def voronoi_generator(self) -> VoronoiGenerator:
        """
        Returns the voronoi generator.
        """
        return self._voronoi_generator
        
    @voronoi_generator.setter
    def voronoi_generator(self, value: VoronoiGenerator) -> None:
        """
        Sets the voronoi generator.
        """
        self._voronoi_generator = value

    @property
    def point_manager(self) -> PointManager:
        """
        Returns the point manager.
        """
        return self._point_manager
        
    @point_manager.setter
    def point_manager(self, value: PointManager) -> None:
        """
        Sets the point manager.
        """
        self._point_manager = value

    @property
    def visualizer(self) -> Visualizer:
        """
        Returns the visualizer.
        """
        return self._visualizer
        
    @visualizer.setter
    def visualizer(self, value: Visualizer) -> None:
        """
        Sets the visualizer.
        """
        self._visualizer = value

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

    def apply_template(
        self,
        point_collection: PointCollection,
        template_type: TemplateType,
        config: TemplateConfig,
        **kwargs
    ) -> 'MapManager':
        """
        Apply a template to the map.
        
        Args:
            template_type: Enum value of the template to apply
            point_collection: Collection of points (creates new if None)
            config: Optional configuration 
            **kwargs: Additional parameters
            
        Returns:
            MapManager: Self for method chaining
        """
        self.template_manager.apply_template(self, point_collection, template_type, config, **kwargs)
        return self
    
    # Convenience methods for common templates
    def create_fort(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] = (50, 50),
        size: int = 20,
        player_id: PlayerId = PlayerId.ONE,
        gate_type: GateType = GateType.FORTIFIED_GATE,
        **kwargs
    ) -> IMapManager:
        """
        Create a fort on the map.
        
        Args:
            center_point: Center coordinates of the fort
            size: Size of the fort
            player_id: Player who owns the fort
            gate_type: Type of gates to use
            **kwargs: Additional parameters for the template
            
        Returns:
            MapManager: Self for method chaining
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=center_point,
            size=size,
            player_id=player_id,
            gate_type=gate_type
        )
        return self.apply_template(point_collection, TemplateType.FORT, config=config, **kwargs)
    
    def create_oak_forest(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.01,
        group_size: int = 12,
        clumping: int = 5,
        **kwargs
    ) -> PointCollection:
        """
        Create an oak forest on the map.
        
        Args:
            point_collection: Collection of points
            player_id: Player who owns the forest (typically GAIA)
            **kwargs: Additional parameters
            
        Returns:
            MapManager: Self for method chaining
        """
        # Pass the explicit parameters to the template
        return OakForestTemplate.generate(
            self, 
            point_collection, 
            player_id=PlayerId.GAIA, 
            groups_density=groups_density,
            group_size=group_size,
            clumping=clumping,
            **kwargs
        )