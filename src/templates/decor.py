"""
Forest template implementation.
"""
from src.templates.abstract_template import AbstractTemplate
from src.templates.template_decorator import register_template
from src.templates.template_types import TemplateType
from src.map.map_manager import MapManager
from src.units.placers.point_management.point_manager import PointCollection
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from src.common.enums.enum import MapLayerType
from typing import Tuple
import random
from src.map.map_manager import IMapManager


@register_template(TemplateType.OAK_FOREST)
class OakForestTemplate(AbstractTemplate):
    """Template for creating an oak forest"""
    
    def __init__(self, name: str = "Oak Forest", description: str = "Creates an oak forest"):
        self.name = name
        self.description = description
    
    @staticmethod
    def generate(
        map_manager: IMapManager, 
        point_collection: PointCollection, 
        center_point: Tuple[int, int] = (50, 50), 
        size: int = 25, 
        player_id: PlayerId = PlayerId.GAIA,
        density: float = 0.6,
        **kwargs
    ):
        """
        Generate an oak forest on the map.
        
        Args:
            map_manager: The map manager
            point_collection: Collection of points
            center_point: Center of the forest
            size: Size of the forest
            player_id: Player who owns the forest (typically GAIA)
            density: Tree density (0.0 to 1.0)
            **kwargs: Additional parameters
        """
        x, y = center_point
        
        # Define the forest area
        min_x = x - size // 2
        max_x = x + size // 2
        min_y = y - size // 2
        max_y = y + size // 2
        
        # Create a more natural forest shape by varying the radius
        num_trees = int((size * size) * density)
        
        # Set terrain to grass for the forest area
        for forest_x in range(min_x, max_x + 1):
            for forest_y in range(min_y, max_y + 1):
                # Calculate distance from center
                distance = ((forest_x - x) ** 2 + (forest_y - y) ** 2) ** 0.5
                
                # Only modify terrain within a circular area
                if distance <= size // 2:
                    map_manager.get_map_layer(MapLayerType.TERRAIN).add_object(
                        forest_x, forest_y, TerrainId.GRASS_1, PlayerId.GAIA
                    )
        
        # Place trees with random distribution
        for _ in range(num_trees):
            # Generate random positions within the forest area
            rand_x = random.randint(min_x, max_x)
            rand_y = random.randint(min_y, max_y)
            
            # Calculate distance from center
            distance = ((rand_x - x) ** 2 + (rand_y - y) ** 2) ** 0.5
            
            # Only place trees within a circular area
            if distance <= size // 2:
                # Randomize tree type
                tree_type = random.choice([
                    UnitInfo.FOREST_TREE, 
                    UnitInfo.OAK_FOREST_TREE
                ])
                
                map_manager.get_map_layer(MapLayerType.UNIT).add_object(
                    rand_x, rand_y, tree_type, player_id
                )


@register_template(TemplateType.SNOW_FOREST)
class SnowForestTemplate(AbstractTemplate):
    """Template for creating a snow forest"""
    
    def __init__(self, name: str = "Snow Forest", description: str = "Creates a snow forest"):
        self.name = name
        self.description = description
    
    @staticmethod
    def generate(
        map_manager: IMapManager, 
        point_collection: PointCollection, 
        center_point: Tuple[int, int] = (50, 50), 
        size: int = 25, 
        player_id: PlayerId = PlayerId.GAIA,
        density: float = 0.6,
        **kwargs
    ):
        """
        Generate a snow forest on the map.
        
        Args:
            map_manager: The map manager
            point_collection: Collection of points
            center_point: Center of the forest
            size: Size of the forest
            player_id: Player who owns the forest (typically GAIA)
            density: Tree density (0.0 to 1.0)
            **kwargs: Additional parameters
        """
        x, y = center_point
        
        # Define the forest area
        min_x = x - size // 2
        max_x = x + size // 2
        min_y = y - size // 2
        max_y = y + size // 2
        
        # Create a more natural forest shape by varying the radius
        num_trees = int((size * size) * density)
        
        # Set terrain to snow for the forest area
        for forest_x in range(min_x, max_x + 1):
            for forest_y in range(min_y, max_y + 1):
                # Calculate distance from center
                distance = ((forest_x - x) ** 2 + (forest_y - y) ** 2) ** 0.5
                
                # Only modify terrain within a circular area
                if distance <= size // 2:
                    map_manager.get_map_layer(MapLayerType.TERRAIN).add_object(
                        forest_x, forest_y, TerrainId.SNOW, PlayerId.GAIA
                    )
        
        # Place trees with random distribution
        for _ in range(num_trees):
            # Generate random positions within the forest area
            rand_x = random.randint(min_x, max_x)
            rand_y = random.randint(min_y, max_y)
            
            # Calculate distance from center
            distance = ((rand_x - x) ** 2 + (rand_y - y) ** 2) ** 0.5
            
            # Only place trees within a circular area
            if distance <= size // 2:
                # Randomize tree type
                tree_type = random.choice([
                    UnitInfo.SNOW_PINE_TREE, 
                    UnitInfo.PINE_FOREST_TREE
                ])
                
                map_manager.get_map_layer(MapLayerType.UNIT).add_object(
                    rand_x, rand_y, tree_type, player_id
                )
