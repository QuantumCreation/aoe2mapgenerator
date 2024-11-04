"""
Manages writing the internal map type to the AOE2 scenario file.
"""

import os
import random

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from aoe2mapgenerator.src.common.constants.constants import (
    BASE_SCENARIO_NAME,
    BASE_SCENE_DIR_LINUX,
    X_SHIFT,
    Y_SHIFT,
)
from aoe2mapgenerator.src.common.enums.enum import (
    GateType,
    MapLayerType,
    ObjectRotation,
    ObjectSize,
)
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.common.types import AOE2ObjectType
from aoe2mapgenerator.src.units.placers.point_selector import PointSelector
from aoe2mapgenerator.src.units.placers.placer_configs import PointSelectorConfig
from aoe2mapgenerator.src.scenario.gate import get_gate_x_shift, get_gate_y_shift


class Scenario:
    """
    Handles creating and writing to the AOE2 scenario file.
    """

    def __init__(
        self,
        aoe2_map: Map,
        base_scenario_full_path: str = os.path.join(
            BASE_SCENE_DIR_LINUX, BASE_SCENARIO_NAME
        ),
    ) -> None:
        """
        Creates a scenario with the given name.

        Args:
            map (Map): Map object to write to the scenario.
            base_scenario_full_path (str, optional): Path to the base scenario file. Defaults to BASE_SCENARIO_FULL_PATH.
        """
        self.scenario = self._get_scenario(base_scenario_full_path)
        self.map = aoe2_map

    def _get_scenario(self, file_full_path: str) -> AoE2DEScenario:
        """
        Loads a scenario from the given file name.

        Args:
            file_full_path (str): Full path to the scenario file.
        """
        return AoE2DEScenario.from_file(file_full_path)

    def write_map(self) -> None:
        """
        Writes to all map layers.
        """
        self._write_any_type(MapLayerType.UNIT)
        self._write_any_type(MapLayerType.TERRAIN)
        self._write_any_type(MapLayerType.DECOR)

    def _write_any_type(self, map_layer_type: MapLayerType) -> None:
        """
        Writes to any type of map layer. Points are retrieved from the scenario's map object

        Args:
            map_layer_type (MapLayerType): Type of map layer to write to.
        """
        # HAS TO BE CHANGED ***** Wrote this a long while ago. IDK what needs to be changed LMAO
        d = self.map.get_dictionary_from_map_layer_type(map_layer_type)
        point_selector = PointSelector(self.map)

        for map_object in d:
            (aoe2_object, player_id) = (
                map_object.get_obj_type(),
                map_object.get_player_id(),
            )

            points = point_selector.get_points_from_map_layer(
                PointSelectorConfig(map_layer_type, map_object)
            )

            if isinstance(aoe2_object, TerrainId):
                self._write_terrain(points, aoe2_object)
            if isinstance(aoe2_object, (BuildingInfo, OtherInfo, UnitInfo)):
                self._write_units(points, aoe2_object, player_id)

    def _write_units(
        self, points: set, aoe2_object: AOE2ObjectType, player: int, rotation: int = -1
    ) -> None:
        """
        Takes a scenario and a list of points to create units in the corresponding positions.

        Args:
            scenario (Scenario): Scenario object to place units.
            points (set): Point positions to place objects.
            unit_const (UnitInfo): AOE2 constant representing unit.
            player (int): Player id of the unit.
            rotation (int, optional): Rotation of the unit. Defaults to -1.
        """
        # HOUSE ROTATION STILL DOES NOT WORK. IDK WHY
        unit_manager = self.scenario.unit_manager
        rotation = 0

        for i, (x, y) in enumerate(points):
            # Adds a random rotation to each unit
            rotation = random.random() * (ObjectRotation(aoe2_object._name_).value)

            # WANKY JANKY CODING. WANT TO IMPROVE.
            if ObjectSize(aoe2_object._name_).value % 2 == 0:
                unit_manager.add_unit(
                    player=player,
                    unit_const=aoe2_object.ID,
                    x=x,
                    y=y,
                    rotation=rotation,
                )
            elif any(
                gate_object.value == aoe2_object._name_ for gate_object in GateObject
            ):
                unit_manager.add_unit(
                    player=player,
                    unit_const=aoe2_object.ID,
                    x=x + get_gate_x_shift(aoe2_object._name_),
                    y=y + get_gate_y_shift(aoe2_object._name_),
                    rotation=rotation,
                )
            else:
                unit_manager.add_unit(
                    player=player,
                    unit_const=aoe2_object.ID,
                    x=x + X_SHIFT,
                    y=y + Y_SHIFT,
                    rotation=rotation,
                )

    def _write_terrain(self, points: set, terrain_const: TerrainId) -> None:
        """
        Takes a scenario and a list of points to create units in the corresponding positions.

        Args:
            points (set): Point positions to place objects.
            terrain_const (TerrainId): AOE2 constant representing unit.
        """
        map_manager = self.scenario.map_manager

        for i, (x, y) in enumerate(points):
            tile = map_manager.get_tile(x, y)
            tile.terrain_id = terrain_const.value

    def _change_map_size(self, map_size: int) -> None:
        """
        Changes the map size.

        Args:
            map_size (int): Size of the map.
        """
        map_manager = self.scenario.map_manager

        map_manager.map_size = map_size

    def save_file(self, output_file_full_path: str) -> None:
        """
        Saves the scenario to the given output file name.

        Args:
            output_file_full_path (str): Full path to the output file.
        """
        self.scenario.write_to_file(output_file_full_path)
