"""
Interface for the MapManager.
"""

from typing import Protocol, List, Tuple, Dict, Set, Any, TypeVar
from src.common.enums.enum import MapLayerType
from src.map.map import Map
from src.map.map_object import MapObject
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
from src.units.placers.placer_base import PlacerBase
from src.units.placers.wall_placer import WallPlacer
from src.units.placers.gate_placer import GatePlacer
from src.units.placers.group_placer import GroupPlacer
from src.units.wallgenerators.voronoi import VoronoiGenerator
from src.visualizer.visualizer import Visualizer


# Type for self-referencing the implementing class
T = TypeVar('T', bound='IMapManager')

class IMapManager(Protocol):
    """
    Protocol defining the interface for the MapManager class.
    """
    @property
    def map(self) -> Map: ...
        
    @map.setter
    def map(self, value: Map) -> None: ...

    @property
    def base_placer(self) -> PlacerBase: ...
        
    @base_placer.setter
    def base_placer(self, value: PlacerBase) -> None: ...

    @property
    def gate_placer(self) -> GatePlacer: ...
        
    @gate_placer.setter
    def gate_placer(self, value: GatePlacer) -> None: ...

    @property
    def group_placer(self) -> GroupPlacer: ...
        
    @group_placer.setter
    def group_placer(self, value: GroupPlacer) -> None: ...

    @property
    def output_dir(self) -> str: ...
        
    @output_dir.setter
    def output_dir(self, value: str) -> None: ...

    @property
    def point_manager(self) -> PointManager: ...
        
    @point_manager.setter
    def point_manager(self, value: PointManager) -> None: ...

    @property
    def scenario(self) -> Scenario: ...
        
    @scenario.setter
    def scenario(self, value: Scenario) -> None: ...

    @property
    def templates(self) -> list: ...
        
    @templates.setter
    def templates(self, value: list) -> None: ...

    @property
    def visualizer(self) -> Visualizer: ...
        
    @visualizer.setter
    def visualizer(self, value: Visualizer) -> None: ...

    @property
    def voronoi_generator(self) -> VoronoiGenerator: ...
        
    @voronoi_generator.setter
    def voronoi_generator(self, value: VoronoiGenerator) -> None: ...

    @property
    def wall_placer(self) -> WallPlacer: ...
        
    @wall_placer.setter
    def wall_placer(self, value: WallPlacer) -> None: ...

    def write_map_and_save(self: T, file_name: str) -> T:
        """
        Writes the map and saves it to a file.
        
        Returns:
            Self for method chaining.
        """
        ...
    
    def place_groups(self: T, configuration: PlaceGroupsConfig) -> T:
        """
        Places groups of objects on the map.
        
        Returns:
            Self for method chaining.
        """
        ...
    
    def place_borders(self: T, configuration: AddBordersConfig) -> T:
        """
        Adds borders to the map.
        
        Returns:
            Self for method chaining.
        """
        ...
    
    def place_voronoi_zones(self: T, configuration: VoronoiGeneratorConfig) -> List[MapObject]:
        """
        Generates the voronoi zones.
        
        Returns:
            Self for method chaining.
        """
        ...
    
    def visualize_map(self: T, configuration: VisualizeMapConfig) -> T:
        """
        Visualizes the map.
        
        Returns:
            Self for method chaining.
        """
        ...
    
    def select_points(self: T, configuration: PointSelectorConfig) -> List[Tuple[int, int]]:
        """
        Selects points on the map.
        Note: This method doesn't support chaining as it returns the selected points.
        """
        ...
    
    def get_map(self: T) -> Map:
        """
        Returns the map object.
        """
        ...
    
    def get_map_layer(self: T, map_layer_type: MapLayerType) -> Any:
        """
        Returns the map layer object.
        """
        ...
    
    def get_dictionary(self: T, map_layer_type: MapLayerType) -> Dict:
        """
        Returns the dictionary of the map layer.
        """
        ...
    
    def get_array(self: T, map_layer_type: MapLayerType) -> List:
        """
        Returns the array of the map layer.
        """
        ...
    
    def get_set_with_map_object(self: T, map_layer_type: MapLayerType, obj: MapObject) -> Set:
        """
        Returns the set of points with the object.
        """
        ...
    
    def get_points_from_map_layer(self: T, configuration: PointSelectorConfig) -> List[Tuple[int, int]]:
        """
        Gets the points from a map layer.
        """
        ...
    
    def points(self: T) -> PointManager:
        """
        Access the point manager to work with point collections.
        This provides a cleaner interface for chaining point operations.
        
        Returns:
            The point manager instance
        """
        ...
        
    # Commented out methods to match the commented methods in MapManager
    # Keep these in the interface but commented out to maintain alignment

    # def apply_template(
    #     self,
    #     template_type: TemplateType,
    #     point_collection: Optional[PointCollection] = None,
    #     config: Optional[TemplateConfig] = None,
    #     **kwargs
    # ) -> T:
    #     """
    #     Apply a template to the map.
    #     
    #     Args:
    #         template_type: Enum value of the template to apply
    #         point_collection: Collection of points (creates new if None)
    #         config: Optional configuration 
    #         **kwargs: Additional parameters
    #         
    #     Returns:
    #         Self for method chaining
    #     """
    #     ...
    
    # def create_fort(
    #     self,
    #     center_point: Tuple[int, int] = (50, 50),
    #     size: int = 20,
    #     player_id: PlayerId = PlayerId.ONE,
    #     gate_type: GateType = GateType.FORTIFIED_GATE,
    #     **kwargs
    # ) -> T:
    #     """
    #     Create a fort on the map.
    #     
    #     Args:
    #         center_point: Center coordinates of the fort
    #         size: Size of the fort
    #         player_id: Player who owns the fort
    #         gate_type: Type of gates to use
    #         **kwargs: Additional parameters for the template
    #         
    #     Returns:
    #         Self for method chaining
    #     """
    #     ...