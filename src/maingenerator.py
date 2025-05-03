# Generator base
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from src.common.enums.enum import (
    MapLayerType,
    ObjectSize,
    GateType,
    TemplateTypes,
    ObjectRotation,
    YamlReplacementKeywords,
    CheckPlacementReturnTypes,
)

from src.scenario.scenario import Scenario
import numpy as np
import random
from src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    BASE_SCENE_DIR_LINUX,
    BASE_SCENARIO_NAME,
    TEMPLATE_DIR_LINUX,
)
from src.common.constants.default_objects import (
    GHOST_OBJECT_DISPLACEMENT,
)
from src.common.enums.enum import GateType
import multiprocessing as mp
from src.map.map import Map
import os
from src.triggers.triggers import TriggerManager
import inspect
import ast
import json
from enum import Enum
from src.units.wallgenerators.voronoi import VoronoiGenerator
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from src.units.placers.statictemplate import TemplateCreator
from src.units.placers.group_placer import GroupPlacer
from src.units.placers.point_management.point_manager import (
    PointCollection,
)
from src.testing import awesome_function
from src.map.map_object import MapObject
from src.units.placers.point_management.point_selector import (
    PointSelector,
)
from src.visualizer.visualizer import Visualizer
from src.units.placers.gate_placer import GatePlacer
from src.units.placers.wall_placer import WallPlacer
from src.map.map_manager import MapManager
from src.units.placers.placer_configs import *
from src.units.placers.placer_configs import PlaceGroupsConfig
import dataclasses
import json
