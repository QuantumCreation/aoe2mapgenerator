from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable, List
import numpy as np

from aoe2mapgenerator.common.constants.constants import DEFAULT_EMPTY_VALUE, DEFAULT_OBJECT_AND_PLAYER
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from dataclasses import dataclass

DisplacementPlaceholder = int

class MapObject():

    def __init__(self, obj_type: AOE2ObjectType | DisplacementPlaceholder, player_id: PlayerId):
        self.obj_type = obj_type
        self.player_id = player_id

    def __hash__(self):
        return hash((self.obj_type, self.player_id))
    
    def __eq__(self, other):
        # Ensure the other object is an instance of CustomObject
        if isinstance(other, MapObject):
            return (self.obj_type, self.player_id) == (other.obj_type, other.player_id)
        return False
