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
from src.templates.gate_utility import generate_polygon_walls_with_gates
from src.common.enums.enum import GateType
from src.templates.decor import AutumnDecor
from typing import Tuple


class FortTemplate(AbstractTemplate):
    """
    Class for placing decor on the map.
    """

    @staticmethod
    def generate2(
        map_manager: MapManager,
        point_collection: PointCollection,
        center_point: Tuple[int, int],
        sides: int = 8,
        radius: int = 12,
    ) -> None:
        """
        Places Autumn decor on the map.

        Args:
            point_manager (PointManager): Manager holding all potential points available for placement
            map_manager (MapManager): Manages the map.
        """

        distance_from_center = 10
        map_layer_type = MapLayerType.UNIT

        generate_polygon_walls_with_gates(
            map_manager=map_manager,
            point_collection=point_collection,
            point=center_point,
            sides=sides,
            radius=radius,
            gate_type=GateType.FORTIFIED_GATE,
        )

        # AutumnDecor.generate(map_manager, point_collection)
