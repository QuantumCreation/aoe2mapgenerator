import random
from re import A
from site import abs_paths
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from map.map_utils import MapUtilsMixin
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize
from AoE2ScenarioParser.datasets.players import PlayerId
from objectplacer import PlacerMixin

class TemplatePlacerMixin(PlacerMixin):
    """
    TODO
    """
