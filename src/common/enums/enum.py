"""
Enum file for the different enums used in the project.
"""

from enum import Enum
import numpy as np
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.support.info_dataset_base import InfoDatasetBase


class MapLayerType(Enum):
    """
    Enum defining the what type a certain value is.
    """

    UNIT = 0
    TERRAIN = 1
    DECOR = 2
    ZONE = 3
    ELEVATION = 4

    @classmethod
    def _missing_(cls, value):
        if value in cls.__members__:
            return cls.__members__[value]
        return cls.UNIT


class ObjectSize(Enum):
    """
    Enum defining the size of the given object.
    """

    # DEFAULT
    DEFAULT_OBJECT_SIZE = 1

    # TERRAIN ASSUMED TO HAVE SIZE 1 VIA DEFAULT

    # BUILDINGS
    CASTLE = 4
    HOUSE = 2
    BARRACKS = 3
    ARCHERY_RANGE = 3
    STABLE = 3
    TOWN_CENTER = 4
    FARM = 3
    MILL = 2
    BURNED_BUILDING = 3
    DONJON = 2
    FORTRESS = 4
    MONASTERY = 3

    SNOW_MOUNTAIN_1 = 5
    SNOW_MOUNTAIN_2 = 5
    SNOW_MOUNTAIN_3 = 5

    # MISC
    ROMAN_RUINS = 2

    # DECOR OBJECTS
    GRASS_PATCH_GREEN = 3
    FLOWER_BED = 2
    FLOWERS_1 = 5
    FLOWERS_2 = 5
    FLOWERS_3 = 5

    @classmethod
    def _missing_(cls, value):
        if value in cls.__members__:
            return cls.__members__[value]
        return cls.DEFAULT_OBJECT_SIZE


class ObjectRotation(Enum):
    """
    Gives the number of rotations an object can have.
    """

    BASIC = 0
    DEFAULT_OBJECT_ROTATION = 2 * np.pi

    # TREES and BUSHES
    TREE_DEFAULT = 42
    TREE_SNOW_PINE = 26
    BUSH_DEFAULT = 4
    FORAGE_BUSH = 4

    # HOUSE ROTATION STILL NOT WORKING! AHSDFHASGHHASDHFAHSDHFAHSDF!?!?!?!
    HOUSE = 3
    BURNED_BUILDING = 12

    @classmethod
    def _missing_(cls, value):

        if value in cls.__members__:
            return cls.__members__[value]

        if "TREE" in value:
            return cls.TREE_DEFAULT

        return cls.DEFAULT_OBJECT_ROTATION


class TemplateSize(Enum):
    """
    Enum defining the size of a given template.
    """


class Directions(Enum):
    """
    Enum of different directions.
    """

    # I DONT THINK THESE ACTUALLY MATCH WHATS GOING ON IN AOE2. I PICKED THEM RANDOMLY.
    NORTH: tuple[int, int] = (-1, 0)
    SOUTH: tuple[int, int] = (1, 0)
    EAST: tuple[int, int] = (0, 1)
    WEST: tuple[int, int] = (0, -1)
    NORTHEAST: tuple[int, int] = (-1, 1)
    NORTHWEST: tuple[int, int] = (-1, -1)
    SOUTHEAST: tuple[int, int] = (1, 1)
    SOUTHWEST: tuple[int, int] = (1, -1)

    @classmethod
    def _missing_(cls, value):
        if value in cls.__members__:
            return cls.__members__[value]
        return cls.NORTH


# Endings for different gate types. This is ugly at the moment. Should probably be improved later on.
def add_endings(gate_name) -> tuple[str, ...]:
    """
    Adds the different endings to the gate type.
    """
    endings: list[str] = [
        "WEST_TO_EAST",
        "NORTH_TO_SOUTH",
        "NORTHWEST_TO_SOUTHEAST",
        "SOUTHWEST_TO_NORTHEAST",
    ]
    result = tuple((f"{gate_name}_{ending}" for ending in endings))
    return result


class GateType(Enum):
    """
    Enum to match gate types with their different versions.
    """

    CITY_GATE = "CITY_GATE"
    FORTIFIED_GATE = "FORTIFIED_GATE"
    PALISADE_GATE = "PALISADE_GATE"
    SEA_GATE = "SEA_GATE"
    STONE_GATE = "STONE_GATE"

    def get_building_info_wall(
        self,
    ) -> BuildingInfo:
        """
        Gets the building info for the wall.

        Args:
            gate_type: The gate type.
        """
        if self == GateType.CITY_GATE:
            return BuildingInfo.CITY_WALL
        if self == GateType.FORTIFIED_GATE:
            return BuildingInfo.FORTIFIED_WALL
        if self == GateType.PALISADE_GATE:
            return BuildingInfo.PALISADE_WALL
        if self == GateType.SEA_GATE:
            return BuildingInfo.SEA_WALL
        if self == GateType.STONE_GATE:
            return BuildingInfo.STONE_WALL
        else:
            raise ValueError(f"Unknown gate type: {self}")

    @staticmethod
    def get_gate_objects_from_gate_type(
        gate_type: "GateType",
    ) -> list["GateObject"]:
        """
        Gets the different gate names from the gate type.

        Args:
            gate_type: The gate type.
        """
        if gate_type == GateType.CITY_GATE:
            return [
                GateObject.CITY_GATE_NORTH_TO_SOUTH,
                GateObject.CITY_GATE_WEST_TO_EAST,
                GateObject.CITY_GATE_NORTHWEST_TO_SOUTHEAST,
                GateObject.CITY_GATE_SOUTHWEST_TO_NORTHEAST,
            ]
        if gate_type == GateType.FORTIFIED_GATE:
            return [
                GateObject.FORTIFIED_GATE_NORTH_TO_SOUTH,
                GateObject.FORTIFIED_GATE_WEST_TO_EAST,
                GateObject.FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST,
                GateObject.FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST,
            ]
        if gate_type == GateType.PALISADE_GATE:
            return [
                GateObject.PALISADE_GATE_NORTH_TO_SOUTH,
                GateObject.PALISADE_GATE_WEST_TO_EAST,
                GateObject.PALISADE_GATE_NORTHWEST_TO_SOUTHEAST,
                GateObject.PALISADE_GATE_SOUTHWEST_TO_NORTHEAST,
            ]
        if gate_type == GateType.SEA_GATE:
            return [
                GateObject.SEA_GATE_NORTH_TO_SOUTH,
                GateObject.SEA_GATE_WEST_TO_EAST,
                GateObject.SEA_GATE_NORTHWEST_TO_SOUTHEAST,
                GateObject.SEA_GATE_SOUTHWEST_TO_NORTHEAST,
            ]
        if gate_type == GateType.STONE_GATE:
            return [
                GateObject.GATE_NORTH_TO_SOUTH,
                GateObject.GATE_WEST_TO_EAST,
                GateObject.GATE_NORTHWEST_TO_SOUTHEAST,
                GateObject.GATE_SOUTHWEST_TO_NORTHEAST,
            ]
        else:
            raise ValueError(f"Unknown gate type: {gate_type}")


class GateObject(Enum):
    """
    Enum to match gate types with their different versions.
    """

    CITY_GATE_NORTH_TO_SOUTH = "CITY_GATE_NORTH_TO_SOUTH"
    CITY_GATE_WEST_TO_EAST = "CITY_GATE_WEST_TO_EAST"
    CITY_GATE_NORTHWEST_TO_SOUTHEAST = "CITY_GATE_NORTHWEST_TO_SOUTHEAST"
    CITY_GATE_SOUTHWEST_TO_NORTHEAST = "CITY_GATE_SOUTHWEST_TO_NORTHEAST"

    FORTIFIED_GATE_NORTH_TO_SOUTH = "FORTIFIED_GATE_NORTH_TO_SOUTH"
    FORTIFIED_GATE_WEST_TO_EAST = "FORTIFIED_GATE_WEST_TO_EAST"
    FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST = "FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST"
    FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST = "FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST"

    PALISADE_GATE_NORTH_TO_SOUTH = "PALISADE_GATE_NORTH_TO_SOUTH"
    PALISADE_GATE_WEST_TO_EAST = "PALISADE_GATE_WEST_TO_EAST"
    PALISADE_GATE_NORTHWEST_TO_SOUTHEAST = "PALISADE_GATE_NORTHWEST_TO_SOUTHEAST"
    PALISADE_GATE_SOUTHWEST_TO_NORTHEAST = "PALISADE_GATE_SOUTHWEST_TO_NORTHEAST"

    SEA_GATE_NORTH_TO_SOUTH = "SEA_GATE_NORTH_TO_SOUTH"
    SEA_GATE_WEST_TO_EAST = "SEA_GATE_WEST_TO_EAST"
    SEA_GATE_NORTHWEST_TO_SOUTHEAST = "SEA_GATE_NORTHWEST_TO_SOUTHEAST"
    SEA_GATE_SOUTHWEST_TO_NORTHEAST = "SEA_GATE_SOUTHWEST_TO_NORTHEAST"

    # Stone walls and gates don't have STONE in front for some stupid reason
    GATE_NORTH_TO_SOUTH = "GATE_NORTH_TO_SOUTH"
    GATE_WEST_TO_EAST = "GATE_WEST_TO_EAST"
    GATE_NORTHWEST_TO_SOUTHEAST = "GATE_NORTHWEST_TO_SOUTHEAST"
    GATE_SOUTHWEST_TO_NORTHEAST = "GATE_SOUTHWEST_TO_NORTHEAST"

    """
    The city gates are the only ones that follow a different pattern for directions than the rest.
    E.G. north for a city gate is not north for palisade gates, etc.
    """

    def get_gate_dimensions(self) -> tuple[tuple[int, int], ...]:
        """
        Gets the dimensions of the gate object.

        Args:
            gate_object: The gate object.
        """
        if self in [
            GateObject.CITY_GATE_NORTH_TO_SOUTH,
            GateObject.FORTIFIED_GATE_NORTH_TO_SOUTH,
            GateObject.PALISADE_GATE_NORTH_TO_SOUTH,
            GateObject.SEA_GATE_NORTH_TO_SOUTH,
            GateObject.GATE_NORTH_TO_SOUTH,
        ]:
            return ((0, 0), (1, -1), (2, -2), (3, -3))
        if self in [
            GateObject.CITY_GATE_WEST_TO_EAST,
            GateObject.FORTIFIED_GATE_WEST_TO_EAST,
            GateObject.PALISADE_GATE_WEST_TO_EAST,
            GateObject.SEA_GATE_WEST_TO_EAST,
            GateObject.GATE_WEST_TO_EAST,
        ]:
            return ((0, 0), (1, 1), (2, 2), (3, 3))
        if self in [
            GateObject.CITY_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.PALISADE_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.SEA_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.GATE_NORTHWEST_TO_SOUTHEAST,
        ]:
            return ((0, 0), (0, 1), (0, 2), (0, 3))

        if self in [
            GateObject.CITY_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.PALISADE_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.SEA_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.GATE_SOUTHWEST_TO_NORTHEAST,
        ]:
            return ((0, 0), (1, 0), (2, 0), (3, 0))

        raise ValueError(f"Unknown gate type: {self}")


class TemplateTypes(Enum):
    """
    Enum representing the different types of templates.
    """

    DYNAMIC = 0
    STATIC = 1
    MIXED = 2

    @classmethod
    def _missing_(cls, value):
        if value in cls.__members__:
            return cls.__members__[value]
        return cls.DYNAMIC


class YamlReplacementKeywords(Enum):
    """
    Enum of the yaml keywords that get replaced with python varibles.
    """

    # ARRAY SPACE REPLACEMENT VARIABLES
    UNIT = "$UNIT"
    TERRAIN = "$TERRAIN"
    ZONE = "$ZONE"
    DECOR = "$DECOR"
    ELEVATION = "$ELEVATION"

    # PLAYER ID
    PLAYER_ID = "$PLAYER_ID"

    # GATE TYPES
    GATE_TYPE = "$GATE_TYPE"


class CheckPlacementReturnTypes(Enum):
    """
    Return types from the check placement function
    """

    FAIL = 0
    SUCCESS = 1
    SUCCESS_IMPOSSIBLE = 2
