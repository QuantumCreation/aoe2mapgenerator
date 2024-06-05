"""
TODO: Add module description
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    DisplacementType,
)


class MapObject:
    """
    Class for the Age of Empires Map Object
    """

    def __init__(
        self,
        obj_type: AOE2ObjectType | DisplacementType = DEFAULT_EMPTY_VALUE,
        player_id: PlayerId = PlayerId.GAIA,
    ):
        self.obj_type = obj_type
        self.player_id = player_id

    def __hash__(self):
        return hash((self.obj_type, self.player_id))

    def __eq__(self, other):
        # Ensure the other object is an instance of CustomObject
        if isinstance(other, MapObject):
            return (self.obj_type, self.player_id) == (other.obj_type, other.player_id)
        return False
