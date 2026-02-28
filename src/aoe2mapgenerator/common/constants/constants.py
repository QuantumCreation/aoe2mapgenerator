"""
This file contains the constants that are used throughout the project.
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
import os
import tempfile

BASE_SCENARIO_NAME = "BASE_SCENARIO.aoe2scenario"

# Cross-platform default output directory.
# Users should override ``output_dir`` on MapManager to point at their
# AoE2 scenario folder.  This sentinel is safe on any operating system.
DEFAULT_OUTPUT_DIR: str = os.path.join(
    tempfile.gettempdir(), "aoe2mapgenerator_output"
)

# Windows Paths
BASE_SCENE_DIR_WINDOWS = "C:\\Users\\josep\\Games\\Age of Empires 2 DE\\76561198242754748\\resources\\_common\\scenario\\"
TEMPLATE_DIR_WINDOWS = "C:\\Users\\josep\\OneDrive\\Documents\\GitHub\\aoe2mapgenerator\\aoe2mapgenerator\\templates\\example_templates"

# WSL Paths
BASE_SCENE_DIR_WINDOWS_WSL = "/mnt/c/Users/josep/Games/Age of Empires 2 DE/76561198242754748/resources/_common/scenario/"
TEMPLATE_DIR_WINDOWS_WSL = "/mnt/c/Users/josep/OneDrive/Documents/GitHub/aoe2mapgenerator/aoe2mapgenerator/templates/example_templates"
BASE_SCENARIO_FULL_PATH_WINDOWS_WSL = os.path.join(BASE_SCENE_DIR_WINDOWS_WSL, BASE_SCENARIO_NAME)

# Linux Paths — use expanduser so they resolve correctly regardless of username
BASE_SCENE_DIR_LINUX = os.path.join(
    os.path.expanduser("~"),
    ".steam/steam/steamapps/compatdata/813780/pfx/dosdevices/c:/users/steamuser"
    "/Games/Age of Empires 2 DE/76561198242754748/resources/_common/scenario/",
)
TEMPLATE_DIR_LINUX = os.path.join(
    os.path.expanduser("~"),
    "Documents/Projects/aoe2mapgenerator/src/templates/example_templates",
)
LINUX_PROJECT_PATH = os.path.join(
    os.path.expanduser("~"),
    "Documents/Projects/aoe2mapgenerator/",
)

# Unit Test Paths
LINUX_PROJECT_UNIT_TEST_PATH = (
    "/home/joseph/Documents/Projects/aoe2mapgenerator/src/unit_tests/"
)
LINUX_PROJECT_UNIT_TEST_IMAGES_PATH = "/home/joseph/Documents/Projects/aoe2mapgenerator/src/unit_tests/unit_test_result_images"

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

DisplacementType = int
