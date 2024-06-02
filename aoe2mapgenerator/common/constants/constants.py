from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo

"""
Universal constants.
"""

BASE_SCENE_DIR = "C:\\Users\\josep\\Games\\Age of Empires 2 DE\\76561198242754748\\resources\\_common\\scenario\\"
TEMPLATE_DIR = "C:\\Users\\josep\\OneDrive\\Documents\\GitHub\\aoe2mapgenerator\\aoe2mapgenerator\\templates\\example_templates"
BASE_SCENARIO_NAME = "BASE_SCENARIO.aoe2scenario"

BASE_SCENE_DIR_LINUX = "/home/joseph/.steam/steam/steamapps/compatdata/813780/pfx/dosdevices/c:/users/steamuser/Games/Age of Empires 2 DE/76561198242754748/resources/_common/scenario/"
TEMPLATE_DIR_LINUX = "/home/joseph/Documents/Projects/aoe2mapgenerator/aoe2mapgenerator/templates/example_templates"

GHOST_OBJECT_DISPLACEMENT_ID = 999
GHOST_OBJECT_MARGIN_ID = 998

"""
These are used for the displacements for objects that take multiple spaces

For example, a castle has a size of 4x4, but the center of the castle is not in the center of the 4x4 square.
Instead, the center of the castle is one of the middle squares of the 4x4 square - Which is very annoying :(

This is used to displace the squares around the single square on the grid which actually holds the castle object
If every square was filled with the castle object, they you would spawn in 16 castles instead of one castle  
"""
DEFAULT_OBJECT_TYPES = [UnitInfo.LEGIONARY]
DEFAULT_EMPTY_VALUE = 0
DEFAULT_PLAYER = PlayerId.GAIA
DEFAULT_OBJECT_AND_PLAYER = (DEFAULT_EMPTY_VALUE, DEFAULT_PLAYER)

X_SHIFT = 0.5
Y_SHIFT = 0.5