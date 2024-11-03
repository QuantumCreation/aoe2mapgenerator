"""
TODO: Add module description
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.src.common.enums.enum import AOE2ObjectType
from aoe2mapgenerator.src.common.constants.constants import (
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
        self._obj_type = obj_type
        self._player_id = player_id

    def __hash__(self):
        return hash((self._obj_type, self._player_id))

    def __eq__(self, other):
        # Ensure the other object is an instance of CustomObject
        if isinstance(other, MapObject):
            return (self._obj_type, self._player_id) == (
                other._obj_type,
                other._player_id,
            )
        return False

    def get_obj_type(self) -> AOE2ObjectType | DisplacementType:
        """
        Gets the object type.
        """
        return self._obj_type

    def get_player_id(self) -> PlayerId:
        """
        Gets the player id.
        """
        return self._player_id
