"""
Defines classes which place decor on the map
"""

from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
# Remove direct import to break circular dependency
# from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
import dataclasses
import ujson as json
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from aoe2mapgenerator.common.enums.enum import (
    MapLayerType,
)
from aoe2mapgenerator.units.placers.placer_configs import (
    PointSelectorConfig,
    PointSelectorInRangeConfig,
    PlaceClosestToPointConfig,
)
from aoe2mapgenerator.units.placers.gate_utility import AdvancedWallPlacer
from aoe2mapgenerator.common.enums.enum import GateType
from typing import Tuple, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports
from aoe2mapgenerator.map.map_manager import IMapManager
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType

@register_template(TemplateType.VILLAGE)
class VillageTemplate(AbstractTemplate):
    """
    Class for placing decor on the map.
    """

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args, **kwargs
    ) -> PointCollection:
        """
        Places a fort on the map with walls on all sides, gates, and a castle in the middle.

        Args:
            map_manager (IMapManager): Manages the map.
            point_collection (PointCollection): Manager holding all potential points available for placement
            args: Variable length argument list.
            kwargs: Arbitrary keyword arguments.
        """
        # Extract the parameters from kwargs if provided, otherwise use defaults
        radius = kwargs.get('radius', 12)
        player_id = kwargs.get('player_id', PlayerId.ONE)
        center_point = point_collection.get_average_point_position()
        
        # Place a castle in the middle
        castle_config = PlaceClosestToPointConfig(
            point_collection=point_collection,
            map_layer_type=MapLayerType.UNIT,
            obj_type=BuildingInfo.CASTLE,
            starting_point=center_point,
            player_id=player_id,
            margin=0,
        )
        
        map_manager.base_placer.place_closest_to_point(castle_config)


        knight_collection = point_collection.copy()
        knight_collection.filter_by_distance(center_point,
                                           distance=radius,
                                           edit_in_place=True)
        
        # Place groups of knights around the castle./
        knight_groups_config = PlaceGroupsConfig(
            point_collection=knight_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=UnitInfo.KNIGHT,
            player_id=player_id,
            groups=10,  # 4 groups of knights
            group_size=12,  # 5 knights per group
            clumping=5
        )

        map_manager.group_placer.place_groups(knight_groups_config)

        # Place groups of archers around the castle
        archer_collection = knight_collection.copy()
        archer_collection.filter_by_distance(center_point,
                                             distance=radius * 0.8,  # Slightly closer
                                             edit_in_place=True)

        archer_groups_config = PlaceGroupsConfig(
            point_collection=archer_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=UnitInfo.ARCHER,
            player_id=player_id,
            groups=8,  # 8 groups of archers
            group_size=10,  # 10 archers per group
            clumping=4
        )

        map_manager.group_placer.place_groups(archer_groups_config)

        # Place groups of militia around the castle
        militia_collection = archer_collection.copy()
        militia_collection.filter_by_distance(center_point,
                                              distance=radius * 0.6,  # Even closer to castle
                                              edit_in_place=True)

        militia_groups_config = PlaceGroupsConfig(
            point_collection=militia_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=UnitInfo.MILITIA,
            player_id=player_id,
            groups=5,  # 5 groups of militia
            group_size=15,  # 15 militia per group
            clumping=3
        )

        map_manager.group_placer.place_groups(militia_groups_config)

        return militia_collection


