from enum import Enum

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
    DEFAULT_ENUM_VALUE = 1
    CASTLE = 4
    HOUSE = 2
    ROAD_FUNGUS = 1
    

    @classmethod
    def _missing_(cls, name):
        try:
            return cls._member_map_[name]
        except:
            return cls.DEFAULT_ENUM_VALUE
