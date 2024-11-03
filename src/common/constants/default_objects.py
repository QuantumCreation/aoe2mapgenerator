"""
TODO:
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
    GHOST_OBJECT_MARGIN_ID,
)
from aoe2mapgenerator.src.map.map_object import MapObject

GHOST_OBJECT_DISPLACEMENT = MapObject(GHOST_OBJECT_DISPLACEMENT_ID, PlayerId.GAIA)
GHOST_OBJECT_MARGIN = MapObject(GHOST_OBJECT_MARGIN_ID, PlayerId.GAIA)
DEFAULT_EMPTY_OBJECT = MapObject(0, PlayerId.GAIA)


def get_default_map_object():
    """
    Returns the default map object.
    """
    return MapObject(DEFAULT_EMPTY_VALUE, PlayerId.GAIA)
