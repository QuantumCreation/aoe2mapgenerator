from aoe2mapgenerator.common.constants.constants import GHOST_OBJECT_DISPLACEMENT_ID, GHOST_OBJECT_MARGIN_ID
from AoE2ScenarioParser.datasets.players import PlayerId
from aoe2mapgenerator.map.map_object import MapObject

GHOST_OBJECT_DISPLACEMENT = MapObject(GHOST_OBJECT_DISPLACEMENT_ID, PlayerId.GAIA)
GHOST_OBJECT_MARGIN = MapObject(GHOST_OBJECT_MARGIN_ID, PlayerId.GAIA)