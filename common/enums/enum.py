from enum import Enum
import numpy as np

class ValueType(Enum):
    """
    Enum defining the what type a certain value is.
    """

    UNIT = 0
    TERRAIN = 1
    DECOR = 2
    ZONE = 3
    ELEVATION = 4

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

    # MISC
    ROMAN_RUINS = 2

    # DECOR OBJECTS
    GRASS_PATCH_GREEN = 3
    FLOWER_BED = 2
    FLOWERS_1 = 5
    FLOWERS_2 = 5
    FLOWERS_3 = 5


    @classmethod
    def _missing_(cls, name):
        try:
            return cls._member_map_[name]
        except:
            return cls.DEFAULT_OBJECT_SIZE

class ObjectRotation(Enum):
    """
    Gives the number of rotations an object can have.
    """

    BASIC = 0
    DEFAULT_OBJECT_ROTATION = 2*np.pi
    TREE = 42
    HOUSE = 3

    @classmethod
    def _missing_(cls, name):
        try:
            return cls._member_map_[name]
        except:
            if "TREE" in name:
                return cls.TREE
            return cls.DEFAULT_OBJECT_ROTATION

class TemplateSize(Enum):
    """
    Enum defining the size of a given template.
    """


