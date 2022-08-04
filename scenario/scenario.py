

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from common.enums.enum import ValueType
from common.enums.enum import ObjectRotation
from common.constants.constants import BASE_SCENE_DIR, X_SHIFT, Y_SHIFT

import random
import numpy as np
from common.enums.enum import ObjectSize
import os
from map.map import Map
from enum import Enum

class Scenario():
    """
    TODO
    """
    def __init__(self, file_name, map):
        """
        TODO
        """
        self.scenario = self.get_scenario(file_name)
        self.map = map

    def get_scenario(self, file_name):
        """
        Creates a scenario with the given name.

        Args:
            file_name: Name of the file.
        """
        file_path = os.path.join(BASE_SCENE_DIR, file_name)

        return AoE2DEScenario.from_file(file_path)

    def write_units(self, points: set, unit_const, player: int, rotation = -1):
        """
        Takes a scenario and a list of points to create units in the corresponding positions.

        Args:
            scenario: Scenario object to place units.
            points: Point positions to place objects.
            unit_const: AOE2 constant representing unit.
            player: Player id of the unit.
        """
        unit_manager = self.scenario.unit_manager
        print(unit_const._name_)
        print((ObjectRotation(unit_const._name_).value))
        rotation = 0
        for i, (x,y) in enumerate(points):
            # Adds a random rotation to each unit
            
            rotation = random.random()*(ObjectRotation(unit_const._name_).value)

            if ObjectSize(unit_const._name_).value%2 == 0:
                unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x,y=y,rotation=rotation)
            else:
                unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x+X_SHIFT,y=y+Y_SHIFT,rotation=rotation)

    def write_terrain(self, points, terrain_const: TerrainId):
        """
        Takes a scenario and a list of points to create units in the corresponding positions.

        Args:
            points: Point positions to place objects.
            terrain_const: AOE2 constant representing unit.
        """
        map_manager = self.scenario.map_manager

        for i, (x,y) in enumerate(points):
            tile = map_manager.get_tile(x, y)
            tile.terrain_id = terrain_const.value


    def write_any_type(self, value_type):
        """
        TODO
        """
        # HAS TO BE CHANGED
        d = self.map.get_dictionary_from_value_type(value_type)

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

    def write_map(self):
        """
        TODO
        """
        self.write_any_type(ValueType.UNIT)
        self.write_any_type(ValueType.TERRAIN)
        self.write_any_type(ValueType.DECOR)


    def change_map_size(self, map_size):
        """
        Changes the map size.

        Args:
            scenario: Scenario object to place units.
            map_size: Size of the map.
        """
        map_manager = self.scenario.map_manager

        map_manager.map_size = map_size

    def save_file(self, output_name):
        """
        Saves the scenario to the given output file name.
        """
        self.scenario.write_to_file(os.path.join(BASE_SCENE_DIR, output_name))