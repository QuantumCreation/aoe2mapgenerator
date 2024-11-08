"""
Defines classes which place decor on the map
"""

from aoe2mapgenerator.src.generation_scripts.template import AbstractTemplate
from aoe2mapgenerator.src.map.map_manager import MapManager
from aoe2mapgenerator.src.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.src.units.placers.placer_configs import PlaceGroupsConfig
import dataclasses
import ujson as json
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from aoe2mapgenerator.src.common.enums.enum import (
    MapLayerType,
)
from aoe2mapgenerator.src.units.placers.placer_configs import (
    PointSelectorConfig,
    PointSelectorInRangeConfig,
)


class AutumnDecor(AbstractTemplate):
    """
    Class for placing decor on the map.
    """

    @staticmethod
    def generate(point_collection: PointCollection, map_manager: MapManager):
        """
        Places Autumn decor on the map.

        Args:
            point_manager (PointManager): Manager holding all potential points available for placement
            map_manager (MapManager): Manages the map.
        """

        map_layer_type = MapLayerType.UNIT

        decor_objects = [
            OtherInfo.BUSH_A,
            OtherInfo.BUSH_B,
            OtherInfo.BUSH_C,
            OtherInfo.FORAGE_BUSH,
            OtherInfo.FRUIT_BUSH,
            OtherInfo.PLANT_BUSH_GREEN,
            OtherInfo.ROCK_1,
            OtherInfo.ROCK_2,
            OtherInfo.FLOWERS_1,
            OtherInfo.FLOWERS_2,
            OtherInfo.FLOWERS_3,
            OtherInfo.FLOWERS_4,
            OtherInfo.GRASS_GREEN,
            OtherInfo.STONE_MINE,
            OtherInfo.GOLD_MINE,
            UnitInfo.DEER,
            UnitInfo.SHEEP,
        ]

        for decor_object in decor_objects:
            map_manager.place_groups(
                PlaceGroupsConfig(
                    point_collection=point_collection,
                    map_layer_type=map_layer_type,
                    object_type=decor_object,
                    player_id=PlayerId.GAIA,
                    group_size=5,
                    groups_density=0.001,
                    clumping=10,
                )
            )

        # Place the trees
        map_manager.place_groups(
            PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=map_layer_type,
                object_type=OtherInfo.TREE_OAK_AUTUMN,
                player_id=PlayerId.GAIA,
                group_size=15,
                groups_density=0.01,
                clumping=15,
            )
        )

        map_manager.place_groups(
            PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=map_layer_type,
                object_type=OtherInfo.TREE_OAK_AUTUMN,
                player_id=PlayerId.GAIA,
                group_size=50,
                groups_density=0.001,
                clumping=15,
            )
        )

        map_manager.place_groups(
            PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=map_layer_type,
                object_type=OtherInfo.TREE_OAK_AUTUMN,
                player_id=PlayerId.GAIA,
                group_size=250,
                groups_density=0.0001,
                clumping=15,
            )
        )
