from enum import Enum



class ValueType(Enum):
    """
    Enum defining the what type a certain value is.
    """

    UNIT = 0
    TERRAIN = 1
    DECOR = 2
    ZONE = 3