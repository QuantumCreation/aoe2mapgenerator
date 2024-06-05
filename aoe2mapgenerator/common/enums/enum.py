"""
Enum file for the different enums used in the project.
"""

from enum import Enum
import numpy as np
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId


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
    NORTH = (0, 1)
    SOUTH = (0, -1)
    EAST = (1, 0)
    WEST = (-1, 0)

    @classmethod
    def _missing_(cls, value):
        if value in cls.__members__:
            return cls.__members__[value]
        return cls.NORTH


# Endings for different gate types. This is ugly at the moment. Should probably be improved later on.
def add_endings(gate_name) -> tuple[str]:
    """
    Adds the different endings to the gate type.
    """
    endings = [
        "WEST_TO_EAST",
        "NORTH_TO_SOUTH",
        "NORTHWEST_TO_SOUTHEAST",
        "SOUTHWEST_TO_NORTHEAST",
    ]
    return tuple((f"{gate_name}_{ending}" for ending in endings))


class GateTypes(Enum):
    """
    Enum to match gate types with their different versions.
    """

    PALISADE_GATE = add_endings("PALISADE_GATE")
    SEA_GATE = add_endings("SEA_GATE")
    FORTIFIED_GATE = add_endings("FORTIFIED_GATE")
    CITY_GATE = add_endings("CITY_GATE")

    @classmethod
    def _missing_(cls, value):
        if value in cls.__members__:
            return cls.__members__[value]
        return cls.FORTIFIED_GATE


class TemplateTypes(Enum):
    """
        Enum representing the different types of templates.

        Information:
            Dynamic templates actively find open locations to place objects.
            Static templates are rectangular sets of objects that are placed
            as a single chunk.from AoE2ScenarioParser.datasets.players import PlayerId
    from AoE2ScenarioParser.datasets.units import UnitInfo
    from AoE2ScenarioParser.datasets.buildings import BuildingInfo
    from AoE2ScenarioParser.datasets.other import OtherInfo
    from AoE2ScenarioParser.datasets.terrains import TerrainId
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


class AOE2ObjectType(Enum):
    """
    AOE2 Object Type Enum
    """

    UNIT_TYPE = UnitInfo
    BUILDING_TYPE = BuildingInfo
    OTHER_TYPE = OtherInfo
    TERRAIN_TYPE = TerrainId

    # This is a custom type used for defining different zones on the map
    ZONE_TYPE = int

    def get_name(self):
        """
        Returns the name of the object type.
        """
        return self.name
