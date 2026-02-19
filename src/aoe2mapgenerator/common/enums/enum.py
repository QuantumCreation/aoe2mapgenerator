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
    def _missing_(cls, value: object) -> "MapLayerType":
        if isinstance(value, str) and value in cls.__members__:
            return cls.__members__[value]
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


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

    # FIXME: house rotation for HOUSE not yet working
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
    Enum of cardinal and intercardinal directions used for gate/border placement.

    Note: These values represent (row_delta, col_delta) offsets in the
    internal grid coordinate system, which may differ from AoE2 in-game
    compass directions.  Verified correct for gate placement logic — update
    with care.
    """

    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST = (0, 1)
    WEST = (0, -1)
    NORTHEAST = (-1, 1)
    NORTHWEST = (-1, -1)
    SOUTHEAST = (1, 1)
    SOUTHWEST = (1, -1)

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
            return ((-1, 1), (0, 0), (1, -1), (2, -2))
        if self in [
            GateObject.CITY_GATE_WEST_TO_EAST,
            GateObject.FORTIFIED_GATE_WEST_TO_EAST,
            GateObject.PALISADE_GATE_WEST_TO_EAST,
            GateObject.SEA_GATE_WEST_TO_EAST,
            GateObject.GATE_WEST_TO_EAST,
        ]:
            return ((-1, -1), (0, 0), (1, 1), (2, 2))
        if self in [
            GateObject.CITY_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.FORTIFIED_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.PALISADE_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.SEA_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.GATE_NORTHWEST_TO_SOUTHEAST,
        ]:
            return ((0, -1), (0, 0), (0, 1), (0, 2))

        if self in [
            GateObject.CITY_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.FORTIFIED_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.PALISADE_GATE_NORTHWEST_TO_SOUTHEAST,
            GateObject.SEA_GATE_SOUTHWEST_TO_NORTHEAST,
            GateObject.GATE_SOUTHWEST_TO_NORTHEAST,
        ]:
            return ((-1, 0), (0, 0), (1, 0), (2, 0))

        raise ValueError(f"Unknown gate type: {self}")

class CheckPlacementReturnTypes(Enum):
    """
    Return types from the check placement function
    """

    FAIL = 0
    SUCCESS = 1
    SUCCESS_IMPOSSIBLE = 2




class DecorObjectsOverlap(Enum):
    """
    Enum of the different decor objects.
    """

    # FLOWERS
    FLOWER_1 = OtherInfo.FLOWERS_1
    FLOWER_2 = OtherInfo.FLOWERS_2
    FLOWER_3 = OtherInfo.FLOWERS_3
    FLOWER_4 = OtherInfo.FLOWERS_4
    FLOWER_BED = OtherInfo.FLOWER_BED

    # GRASS PATCHES
    GRASS_PATCH_GREEN = OtherInfo.GRASS_PATCH_GREEN
    GRASS_PATCH_BROWN = OtherInfo.GRASS_PATCH_DRY
    GRASS_DRY = OtherInfo.GRASS_DRY
    GRASS_GREEN = OtherInfo.GRASS_GREEN

    # Paths
    PATH_1 = OtherInfo.PATH_1
    PATH_2 = OtherInfo.PATH_2
    PATH_3 = OtherInfo.PATH_3
    PATH_4 = OtherInfo.PATH_4

class ObjectsAnimals(Enum):
    """
    Enum of the different decor objects.
    """

    # ANIMALS
    BEAR = UnitInfo.BEAR
    BUTTERFLY1 = UnitInfo.BUTTERFLY1
    BUTTERFLY2 = UnitInfo.BUTTERFLY2
    BUTTERFLY3 = UnitInfo.BUTTERFLY3
    CROCODILE = UnitInfo.CROCODILE
    DEER = UnitInfo.DEER
    DIRE_WOLF = UnitInfo.DIRE_WOLF
    FALCON = UnitInfo.FALCON
    HAWK = UnitInfo.HAWK
    IBEX = UnitInfo.IBEX
    IRON_BOAR = UnitInfo.IRON_BOAR
    JAGUAR = UnitInfo.JAGUAR
    JAVELINA = UnitInfo.JAVELINA
    KOMODO_DRAGON = UnitInfo.KOMODO_DRAGON
    LION = UnitInfo.LION
    MACAW = UnitInfo.MACAW
    OSTRICH = UnitInfo.OSTRICH
    RABID_WOLF = UnitInfo.RABID_WOLF
    RHINOCEROS = UnitInfo.RHINOCEROS
    SEAGULLS = UnitInfo.SEAGULLS
    SNOW_LEOPARD = UnitInfo.SNOW_LEOPARD
    STORK = UnitInfo.STORK
    TIGER = UnitInfo.TIGER
    VULTURE = UnitInfo.VULTURE
    WILD_BACTRIAN_CAMEL = UnitInfo.WILD_BACTRIAN_CAMEL
    WILD_BOAR = UnitInfo.WILD_BOAR
    WILD_CAMEL = UnitInfo.WILD_CAMEL
    WILD_HORSE = UnitInfo.WILD_HORSE
    WOLF = UnitInfo.WOLF
    ZEBRA = UnitInfo.ZEBRA
    GAZELLE = UnitInfo.GAZELLE

class ObjectResources(Enum):
    """
    Enum of the different resource objects.
    """

    FORAGE_BUSH = OtherInfo.FORAGE_BUSH
    FRUIT_BUSH = OtherInfo.FRUIT_BUSH
    GOLD_MINE = OtherInfo.GOLD_MINE
    STONE_MINE = OtherInfo.STONE_MINE
 

class DecorObjectTakeSpace(Enum):
    """
    Enum of decor objects with their detailed properties.
    """

    BUSH_A = OtherInfo.BUSH_A
    BUSH_B = OtherInfo.BUSH_B
    BUSH_C = OtherInfo.BUSH_C
    CRACKS = OtherInfo.CRACKS
    CRATER = OtherInfo.CRATER
    FORAGE_BUSH = OtherInfo.FORAGE_BUSH
    FRUIT_BUSH = OtherInfo.FRUIT_BUSH
    GOLD_MINE = OtherInfo.GOLD_MINE
    GOTHIC_RELIC = OtherInfo.GOTHIC_RELIC
    GRANARY = OtherInfo.GRANARY
    GRASS_PATCH_DRY = OtherInfo.GRASS_PATCH_DRY
    GRASS_PATCH_GREEN = OtherInfo.GRASS_PATCH_GREEN
    PLANT = OtherInfo.PLANT
    PLANT_BUSH_GREEN = OtherInfo.PLANT_BUSH_GREEN
    PLANT_DEAD = OtherInfo.PLANT_DEAD
    PLANT_FLOWERS = OtherInfo.PLANT_FLOWERS
    PLANT_RAINFOREST = OtherInfo.PLANT_RAINFOREST
    PLANT_SHRUB_GREEN = OtherInfo.PLANT_SHRUB_GREEN
    PLANT_UNDERBRUSH = OtherInfo.PLANT_UNDERBRUSH
    PLANT_WEEDS = OtherInfo.PLANT_WEEDS
    ROCK_1 = OtherInfo.ROCK_1
    ROCK_2 = OtherInfo.ROCK_2
    ROCK_FORMATION_1 = OtherInfo.ROCK_FORMATION_1
    ROCK_FORMATION_2 = OtherInfo.ROCK_FORMATION_2
    ROCK_FORMATION_3 = OtherInfo.ROCK_FORMATION_3
    ROMAN_RUINS = OtherInfo.ROMAN_RUINS
    RUGS = OtherInfo.RUGS
    SARACEN_RELIC = OtherInfo.SARACEN_RELIC
    SEA_ROCKS_1 = OtherInfo.SEA_ROCKS_1
    SEA_ROCKS_2 = OtherInfo.SEA_ROCKS_2
    STONE_MINE = OtherInfo.STONE_MINE
    STUMP = OtherInfo.STUMP
    TEMPLE_RUIN = OtherInfo.TEMPLE_RUIN
    TEUTONIC_RELIC = OtherInfo.TEUTONIC_RELIC
    THE_ACCURSED_TOWER = OtherInfo.THE_ACCURSED_TOWER
    THE_TOWER_OF_FLIES = OtherInfo.THE_TOWER_OF_FLIES
    WELL = OtherInfo.WELL
    WATERFALL_OVERLAY = OtherInfo.WATERFALL_OVERLAY
    QUARRY = OtherInfo.QUARRY
    LUMBER = OtherInfo.LUMBER
    GOODS = OtherInfo.GOODS
