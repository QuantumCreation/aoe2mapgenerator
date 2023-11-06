from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.players import PlayerId

"""
Universal constants.
"""

BASE_SCENE_DIR = "C:\\Users\\josep\\Games\\Age of Empires 2 DE\\76561198242754748\\resources\\_common\\scenario\\"
TEMPLATE_DIR = "C:\\Users\\josep\\OneDrive\\Documents\\GitHub\\aoe2mapgenerator\\aoe2mapgenerator\\templates\\example_templates"
BASE_SCENARIO_NAME = "BASE_SCENARIO.aoe2scenario"

GHOST_OBJECT_DISPLACEMENT = 999
GHOST_OBJECT_MARGIN = 998
DEFAULT_OBJECT_TYPES = []
DEFAULT_EMPTY_VALUE = 0
DEFAULT_PLAYER = PlayerId.GAIA
DEFAULT_OBJECT_AND_PLAYER = (DEFAULT_EMPTY_VALUE, DEFAULT_PLAYER)


X_SHIFT = 0.5
Y_SHIFT = 0.5