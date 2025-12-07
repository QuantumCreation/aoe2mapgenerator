# Generator base
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.common.enums.enum import (
    MapLayerType,
    ObjectSize,
    GateType,
    TemplateTypes,
    ObjectRotation,
    YamlReplacementKeywords,
    CheckPlacementReturnTypes,
)

from aoe2mapgenerator.scenario.scenario import Scenario
import numpy as np
import random
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    BASE_SCENE_DIR_LINUX,
    BASE_SCENARIO_NAME,
    TEMPLATE_DIR_LINUX,
)
from aoe2mapgenerator.common.constants.default_objects import (
    GHOST_OBJECT_DISPLACEMENT,
)
from aoe2mapgenerator.common.enums.enum import GateType
import multiprocessing as mp
from aoe2mapgenerator.map.map import Map
import os
from aoe2mapgenerator.triggers.triggers import TriggerManager
import inspect
import ast
import json
from enum import Enum
from aoe2mapgenerator.units.wallgenerators.voronoi import VoronoiGenerator
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from aoe2mapgenerator.units.placers.statictemplate import TemplateCreator
from aoe2mapgenerator.units.placers.group_placer import GroupPlacer
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.testing import awesome_function
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.point_management.point_selector import (
    PointSelector,
)
from aoe2mapgenerator.visualizer.visualizer import Visualizer
from aoe2mapgenerator.units.placers.gate_placer import GatePlacer
from aoe2mapgenerator.units.placers.wall_placer import WallPlacer
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.units.placers.placer_configs import *
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
import dataclasses
import json
