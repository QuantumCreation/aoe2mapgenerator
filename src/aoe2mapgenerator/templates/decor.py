"""
Forest template implementation.
"""
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.common.enums.enum import MapLayerType
from typing import Tuple
import random
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
from aoe2mapgenerator.common.enums.enum import (
    DecorObjectsOverlap,
    ObjectsAnimals,
    ObjectResources
)

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
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs
    )-> PointCollection:
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
        groups_density = kwargs.get('groups_density', 0.01)
        group_size = kwargs.get('group_size', 12)
        clumping = kwargs.get('clumping', 5)


        point_collection_copy_decor_only = point_collection.copy()

        oak_forest_groups_config = PlaceGroupsConfig(
            point_collection=point_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=OtherInfo.TREE_OAK_AUTUMN,
            player_id=player_id,
            groups_density=groups_density,
            group_size=group_size,
            clumping=clumping
        )

        map_manager.group_placer.place_groups(oak_forest_groups_config)

        # Example of iterating over DecorObjectsOverlap enum
        for decor_object in DecorObjectsOverlap:

            groups_density = 0.001
            group_size = random.randint(2, 5)
            clumping = random.randint(5, 15)

            decor_config = PlaceGroupsConfig(
                point_collection=point_collection_copy_decor_only,
                map_layer_type=MapLayerType.DECOR,
                object_type=decor_object.value,
                player_id=player_id,
                groups_density=groups_density,
                group_size=group_size,
                clumping=clumping
            )

            map_manager.group_placer.place_groups(decor_config)

        filtered_animals = [
            ObjectsAnimals.WOLF,
            ObjectsAnimals.BEAR,
            ObjectsAnimals.DEER,
            ObjectsAnimals.SNOW_LEOPARD
        ]

        for animal in filtered_animals:
            
            groups_density = 0.001
            group_size = random.randint(4, 7)
            clumping = random.randint(5, 10)

            decor_config = PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.UNIT,
                object_type=animal.value,
                player_id=PlayerId.GAIA,
                groups_density=groups_density,
                group_size=group_size,
                clumping=clumping
            )

            map_manager.group_placer.place_groups(decor_config)
        # Add resource objects to the forest

        filtered_resources = [
            ObjectResources.FORAGE_BUSH,
            ObjectResources.FRUIT_BUSH,
            ObjectResources.STONE_MINE,
            ObjectResources.GOLD_MINE
        ]

        for resource in filtered_resources:
            groups_density = 0.0005
            group_size = random.randint(3, 6)
            clumping = random.randint(3, 5)
            
            resource_config = PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.UNIT,
                object_type=resource.value,
                player_id=PlayerId.GAIA,
                groups_density=groups_density,
                group_size=group_size,
                clumping=clumping
            )
            
            map_manager.group_placer.place_groups(resource_config)


        return point_collection

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
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs
    )-> PointCollection:
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

        return point_collection
