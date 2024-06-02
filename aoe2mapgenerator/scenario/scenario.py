

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.common.enums.enum import ObjectRotation, MapLayerType, GateTypes
from aoe2mapgenerator.common.constants.constants import BASE_SCENE_DIR, X_SHIFT, Y_SHIFT, BASE_SCENARIO_NAME

import random
import numpy as np
from aoe2mapgenerator.common.enums.enum import ObjectSize
import os
from aoe2mapgenerator.map.map import Map

class Scenario():
    """
    Handles creating and writing to the AOE2 scenario file.
    """

    def __init__(self, map: Map, base_scenario_full_path: str = os.path.join(BASE_SCENE_DIR, BASE_SCENARIO_NAME)) -> None:
        """
        Creates a scenario with the given name.

        Args:
            map (Map): Map object to write to the scenario. 
            base_scenario_full_path (str, optional): Path to the base scenario file. Defaults to BASE_SCENARIO_FULL_PATH.
        """
        self.scenario = self._get_scenario(base_scenario_full_path)
        self.map = map

    def write_map(self) -> None:
        """
        Writes to all map layers.
        """
        self._write_any_type(MapLayerType.UNIT)
        self._write_any_type(MapLayerType.TERRAIN)
        self._write_any_type(MapLayerType.DECOR)

    def _get_scenario(self, file_full_path: str) -> AoE2DEScenario:
        """
        Loads a scenario from the given file name.

        Args:
            file_full_path (str): Full path to the scenario file.
        """
        return AoE2DEScenario.from_file(file_full_path)

    def _write_units(self, points: set, unit_const, player: int, rotation: int = -1) -> None:
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
        for i, (x,y) in enumerate(points):
            # Adds a random rotation to each unit
            rotation = random.random()*(ObjectRotation(unit_const._name_).value)

            # WANKY JANKY CODING. WANT TO IMPROVE.
            if ObjectSize(unit_const._name_).value%2 == 0:
                unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x,y=y,rotation=rotation)
            elif any(gate_type.value[2]==unit_const._name_ for gate_type in GateTypes):
                unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x+X_SHIFT,y=y,rotation=rotation)
            elif any(gate_type.value[3]==unit_const._name_ for gate_type in GateTypes):
                unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x,y=y+Y_SHIFT,rotation=rotation)
            else:
                unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x+X_SHIFT,y=y+Y_SHIFT,rotation=rotation)

    def _write_terrain(self, points: set, terrain_const: TerrainId) -> None:
        """
        Takes a scenario and a list of points to create units in the corresponding positions.

        Args:
            points (set): Point positions to place objects.
            terrain_const (TerrainId): AOE2 constant representing unit.
        """
        map_manager = self.scenario.map_manager

        for i, (x,y) in enumerate(points):
            tile = map_manager.get_tile(x, y)
            tile.terrain_id = terrain_const.value

    def _write_any_type(self, map_layer_type: MapLayerType) -> None:
        """
        Writes to any type of map layer. Points are retrieved from the scenario's map object

        Args:
            map_layer_type (MapLayerType): Type of map layer to write to.
        """
        # HAS TO BE CHANGED ***** Wrote this a long while ago. IDK what needs to be changed LMAO
        d = self.map.get_dictionary_from_map_layer_type(map_layer_type)

        for key in d:
            if type(key) == tuple:
                (aoe2_object, player_id) = key
            else:
                continue
            
            points = d[(aoe2_object, player_id)]

            if isinstance(aoe2_object, TerrainId):
                self._write_terrain(points, aoe2_object)
            if isinstance(aoe2_object, BuildingInfo) or isinstance(aoe2_object, UnitInfo) or isinstance(aoe2_object, OtherInfo):
                self._write_units(points, aoe2_object, player_id)

    def _change_map_size(self, map_size: int) -> None:
        """
        Changes the map size.

        Args:
            map_size (int): Size of the map.
        """
        map_manager = self.scenario.map_manager

        map_manager.map_size = map_size

    def save_file(self, output_file_full_path) -> None:
        """
        Saves the scenario to the given output file name.

        Args:
            output_file_full_path (str): Full path to the output file.
        """
        self.scenario.write_to_file(output_file_full_path)
