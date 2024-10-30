"""
Manages the placement of gates in the scenario. 
"""

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from aoe2mapgenerator.src.common.constants.constants import (
    BASE_SCENARIO_NAME,
    BASE_SCENE_DIR_LINUX,
    X_SHIFT,
    Y_SHIFT,
)
from aoe2mapgenerator.src.common.enums.enum import (
    GateType,
    MapLayerType,
    ObjectRotation,
    ObjectSize,
)
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.common.enums.enum import AOE2ObjectType, GateObject
from aoe2mapgenerator.src.units.placers.point_selector import PointSelector
from aoe2mapgenerator.src.units.placers.placer_configs import PointSelectorConfig


def get_gate_x_shift(gate_object_string: str):
    """
    Gets the x shift for the given gate object.

    Args:
        gate_object (GateObject): Gate object to get the x shift for.

    WARNING: City gates do not follow the same directions as the rest of the gates.
    North for a city gate is not North for the other gates.
    """
    if gate_object_string in [
        GateObject.CITY_GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.PALISADE_GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.SEA_GATE_SOUTHWEST_TO_NORTHEAST.value,
    ]:
        return 0
    if gate_object_string in [
        GateObject.CITY_GATE_WEST_TO_EAST.value,
        GateObject.FORTIFIED_GATE_WEST_TO_EAST.value,
        GateObject.GATE_WEST_TO_EAST.value,
        GateObject.PALISADE_GATE_WEST_TO_EAST.value,
        GateObject.SEA_GATE_WEST_TO_EAST.value,
    ]:
        return 0
    if gate_object_string in [
        GateObject.CITY_GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.PALISADE_GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.SEA_GATE_NORTHWEST_TO_SOUTHEAST.value,
    ]:
        return X_SHIFT
    if gate_object_string in [
        GateObject.CITY_GATE_NORTH_TO_SOUTH.value,
        GateObject.FORTIFIED_GATE_NORTH_TO_SOUTH.value,
        GateObject.GATE_NORTH_TO_SOUTH.value,
        GateObject.PALISADE_GATE_NORTH_TO_SOUTH.value,
        GateObject.SEA_GATE_NORTH_TO_SOUTH.value,
    ]:
        return 0
    return 0


def get_gate_y_shift(gate_object_string: str):
    """
    Gets the x shift for the given gate object.

    Args:
        gate_object (GateObject): Gate object to get the x shift for.

    WARNING: City gates do not follow the same directions as the rest of the gates.
    North for a city gate is not North for the other gates.
    """
    if gate_object_string in [
        GateObject.CITY_GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.PALISADE_GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.SEA_GATE_SOUTHWEST_TO_NORTHEAST.value,
    ]:
        return Y_SHIFT
    if gate_object_string in [
        GateObject.CITY_GATE_WEST_TO_EAST.value,
        GateObject.FORTIFIED_GATE_WEST_TO_EAST.value,
        GateObject.GATE_WEST_TO_EAST.value,
        GateObject.PALISADE_GATE_WEST_TO_EAST.value,
        GateObject.SEA_GATE_WEST_TO_EAST.value,
    ]:
        return 0
    if gate_object_string in [
        GateObject.CITY_GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.GATE_NORTHWEST_TO_SOUTHEAST.value,
        GateObject.PALISADE_GATE_SOUTHWEST_TO_NORTHEAST.value,
        GateObject.SEA_GATE_NORTHWEST_TO_SOUTHEAST.value,
    ]:
        return 0
    if gate_object_string in [
        GateObject.CITY_GATE_NORTH_TO_SOUTH.value,
        GateObject.FORTIFIED_GATE_NORTH_TO_SOUTH.value,
        GateObject.GATE_NORTH_TO_SOUTH.value,
        GateObject.PALISADE_GATE_NORTH_TO_SOUTH.value,
        GateObject.SEA_GATE_NORTH_TO_SOUTH.value,
    ]:
        return 2 * Y_SHIFT
    return 0
