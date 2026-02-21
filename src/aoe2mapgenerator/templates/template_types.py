"""
Enum definitions for template types.
"""

from enum import Enum, auto

class TemplateType(Enum):
    """Enum for all available map templates"""
    CASTLE = auto()
    FORT = auto()
    VILLAGE = auto()
    FOREST = auto()
    MOUNTAIN = auto()
    RIVER = auto()
    ROAD = auto()
    MINE = auto()
    OAK_FOREST = auto()
    SNOW_FOREST = auto()
    WALLS = auto()
    CITY = auto()
    PALACE = auto()
    # Add more as needed
