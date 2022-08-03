

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId

from common.constants.constants import BASE_SCENE_DIR

from units.placers.buildingplacer import get_valid_points
import random
import numpy as np

import os

X_SHIFT = 0.5
Y_SHIFT = 0.5

input_path = r"C:\Users\josep\Games\Age of Empires 2 DE\76561198242754748\resources\_common\scenario\Basic_Py.aoe2scenario"
output_path = r"C:\Users\josep\Games\Age of Empires 2 DE\76561198242754748\resources\_common\scenario\Basic_Py2.aoe2scenario"

NON_SHIFT_CLASSES = {
    BuildingInfo.CASTLE,
    BuildingInfo.HOUSE,
}

def make_scenario(file_name):
    """
    Creates a scenario with the given name.

    Args:
        file_name: Name of the file.
    """
    file_path = os.path.join(BASE_SCENE_DIR, file_name)

    return AoE2DEScenario.from_file(file_path)

def write_units(scenario, points: set, unit_const, player: int, rotation = -1):
    """
    Takes a scenario and a list of points to create units is the corresponding positions.

    Args:
        scenario: Scenario object to place units.
        points: Point positions to place objects.
        unit_const: AOE2 constant representing unit.
        player: Player id of the unit.
    """
    unit_manager = scenario.unit_manager

    rotation = 0
    for i, (x,y) in enumerate(points):
        rotation = int(random.random()*50)

        if unit_const in NON_SHIFT_CLASSES:
            unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x,y=y,rotation=rotation)
        else:
            unit_manager.add_unit(player=player,unit_const=unit_const.ID,x=x+X_SHIFT,y=y+Y_SHIFT,rotation=rotation)

    return scenario

def write_terrain(scenario, points, terrain_const: TerrainId):
    """
    TODO
    """
    map_manager = scenario.map_manager

    for i, (x,y) in enumerate(points):
        tile = map_manager.get_tile(x, y)
        tile.terrain_id = terrain_const.value

    return scenario

def write_multiple(scenario, map, player: int):
    """
    TODO
    """

    for k in map.object_dict:
        points = map.object_dict[k]

        if type(k) == int:
            continue
    
        if k in BuildingInfo or k in UnitInfo:
            write_units(scenario, points, k, player)
        elif k in OtherInfo:
            write_units(scenario, points, k, PlayerId.GAIA)
        elif k in TerrainId:
            write_terrain(scenario, points, k)
    
    return scenario

def write_map(scenario, map_size):
    """
    Changes the map size.

    Args:
        scenario: Scenario object to place units.
        map_size: Size of the map.
    """
    map_manager = scenario.map_manager

    map_manager.map_size = map_size

    return scenario

def save_file(scenario, output_name):
    """
    Saves the scenario to the given output file name.
    """
    scenario.write_to_file(os.path.join(BASE_SCENE_DIR, output_name))