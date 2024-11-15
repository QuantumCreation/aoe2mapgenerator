"""
Defines classes which place decor on the map
"""

from src.templates.abstract_template import AbstractTemplate
from src.map.map_manager import MapManager
from src.units.placers.point_management.point_manager import (
    PointCollection,
)
from src.units.placers.placer_configs import PlaceGroupsConfig
import dataclasses
import ujson as json
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from src.common.enums.enum import (
    MapLayerType,
)
from src.units.placers.placer_configs import (
    PointSelectorConfig,
    PointSelectorInRangeConfig,
)


class FortTemplate(AbstractTemplate):
    """
    Class for placing decor on the map.
    """

    @staticmethod
    def generate(map_manager: MapManager, point_collection: PointCollection) -> None:
        """
        Places Autumn decor on the map.

        Args:
            point_manager (PointManager): Manager holding all potential points available for placement
            map_manager (MapManager): Manages the map.
        """

        map_layer_type = MapLayerType.UNIT

        config = PlaceGroupsConfig(
            point_collection=point_collection,
            map_layer_type=map_layer_type,
            object_type=OtherInfo.TREE_OAK_AUTUMN,
            player_id=PlayerId.GAIA,
            group_size=250,
            groups_density=0.0001,
            clumping=15,
        )

        map_manager.place_groups(config)
