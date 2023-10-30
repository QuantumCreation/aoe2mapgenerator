

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from common.enums.enum import ObjectRotation, MapLayerType, GateTypes
from common.constants.constants import BASE_SCENE_DIR, X_SHIFT, Y_SHIFT

import random
import numpy as np
from common.enums.enum import ObjectSize
import os
from map.map import Map
from enum import Enum

class Scenario():
    """
    Handles creating and writing to the AOE2 scenario file.
    """

    def __init__(self, base_file_name: str, map: Map, base_file_path: str = BASE_SCENE_DIR) -> None:
        """
        Creates a scenario with the given name.

        Args:
            base_file_name (str): Name of the base scenario file.
            map (Map): Map object to write to the scenario. 
            base_file_path (str, optional): Path to the file. Defaults to "".
        """
        self.scenario = self.get_scenario(base_file_name, base_file_path)
        self.map = map

    def get_scenario(self, file_name: str, file_path: str) -> AoE2DEScenario:
        """
        Loads a scenario from the given file name.

        Args:
            file_name (str): Name of the scenario file.
            file_path (str, optional): Path to the file. Defaults to "".
        """
        full_file_path = os.path.join(file_path, file_name)

        return AoE2DEScenario.from_file(full_file_path)

    def write_units(self, points: set, unit_const, player: int, rotation: int = -1) -> None:
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

    def write_terrain(self, points: set, terrain_const: TerrainId) -> None:
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

    def write_any_type(self, map_layer_type: MapLayerType) -> None:
        """
        Writes to any type of map layer.

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
                self.write_terrain(points, aoe2_object)
            if isinstance(aoe2_object, BuildingInfo) or isinstance(aoe2_object, UnitInfo) or isinstance(aoe2_object, OtherInfo):
                self.write_units(points, aoe2_object, player_id)

    def write_map(self) -> None:
        """
        Writes to all map layers.
        """
        self.write_any_type(MapLayerType.UNIT)
        self.write_any_type(MapLayerType.TERRAIN)
        self.write_any_type(MapLayerType.DECOR)


    def change_map_size(self, map_size: int) -> None:
        """
        Changes the map size.

        Args:
            map_size (int): Size of the map.
        """
        map_manager = self.scenario.map_manager

        map_manager.map_size = map_size

    def save_file(self, output_name: str, output_path: str = BASE_SCENE_DIR) -> None:
        """
        Saves the scenario to the given output file name.

        Args:
            output_name (str): Name of the output file.
            output_path (str, optional): Path to the output file. Defaults to "".
        """
        self.scenario.write_to_file(os.path.join(output_path, output_name))
