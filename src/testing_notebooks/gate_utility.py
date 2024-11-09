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
    DEFAULT_EMPTY_OBJECT,
)
from src.common.enums.enum import GateType
import multiprocessing as mp
from src.map.map import Map
import os
from src.serializer.serializer import (
    _convert_map_value_to_string,
    _get_enum_list,
    _recursive_parse_enum_to_string,
    serialize_map,
    get_all_functions_and_arguments,
    _get_functions,
    _get_function_arguments,
    _get_default_arguments,
    serialize_enum,
)
from src.triggers.triggers import TriggerManager
from src.maingenerator import main_map_generator
import inspect
import ast
import ujson as json
from enum import Enum
from src.units.wallgenerators.voronoi import VoronoiGenerator
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from src.units.placers.statictemplate import TemplateCreator
from src.units.placers.group_placer import GroupPlacerManager
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
import ujson as json
from src.units.wallgenerators.polygon import generate_polygonal_wall


def generate_polygon_walls_with_gates(
    map_manager: MapManager,
    x: int,
    y: int,
    sides: int,
    radius: int,
    gate_type: GateType,
):
    """
    Generates a polygonal wall with gates.

    Args:
        map_manager (MapManager): The map manager.
        x (int): The x coordinate.
        y (int): The y coordinate.
        gate_type (GateType): The type of gate.
    """
    # Generate the polygonal wall points
    points = generate_polygonal_wall(x, y, sides, radius)
    map_manager.point_manager.add_point_collection("wall_points", points)

    # Set the type of wall to use
    wall_type = gate_type.get_building_info_wall()

    # Place points for the wall
    map_manager.base_placer.place_multiple(
        map_manager.point_manager,
        map_layer_type=MapLayerType.UNIT,
        points=points,
        obj_type=wall_type,
        player_id=PlayerId.ONE,
    )

    # Get the points for the wall
    points = map_manager.point_manager.point_selector.get_points_from_map_layer(
        PointSelectorConfig(
            map_layer_type=MapLayerType.UNIT,
            object_type=MapObject(wall_type, player_id=PlayerId.ONE),
        )
    )

    # clear the points and add them
    map_manager.point_manager.clear()
    map_manager.point_manager.add_points(points)

    # Place the gates
    map_manager.gate_placer.place_gate_on_eight_sides(
        point_manager=map_manager.point_manager,
        map_layer_type=MapLayerType.UNIT,
        gate_type=gate_type,
        player_id=PlayerId.ONE,
    )
