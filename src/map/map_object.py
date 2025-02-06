"""
TODO: Add module description
"""

from typing import Any
from AoE2ScenarioParser.datasets.players import PlayerId

from src.common.types import AOE2ObjectType
from src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    DisplacementType,
)

from src.serializer.base_serializer import Serializable
import ujson as json
from src.utils.flywheel_factory import FlywheelFactory


class MapObject(Serializable):
    """
    Class for the Age of Empires Map Object
    """

    # USing a flywheel causes issues elsewhere
    # def __new__(cls, obj_type: AOE2ObjectType, player_id):
    #     """
    #     Returns a cached instance of MapObject if available, otherwise creates a new one.

    #     Args:
    #         obj_type (AOE2ObjectType): The type of object.
    #         player_id (PlayerId): The owner of the object.
    #     """
    #     key = (obj_type, player_id)
    #     return FlywheelFactory.get_instance(
    #         key, lambda: super(MapObject, cls).__new__(cls)
    #     )

    def __init__(
        self,
        obj_type: AOE2ObjectType | DisplacementType = DEFAULT_EMPTY_VALUE,
        player_id: PlayerId = PlayerId.GAIA,
    ):
        self._initialized = True
        self._obj_type = obj_type
        self._player_id = player_id

    def __repr__(self):
        return f"MapObject({self.obj_type}, Player: {self.player_id})"

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

    def to_dict(self):
        return {
            "_type": self.__class__.__name__,
            "_obj_type": self.serialize_prim(self._obj_type),
            "_player_id": self.serialize_prim(self._player_id),
        }

    def serialize(self) -> Any:
        return self.dump(self.to_dict())

    @staticmethod
    def deserialize(json_string: str | dict) -> Any:
        json_dict: dict
        if isinstance(json_string, dict):
            json_dict = json_string
        else:
            json_dict = json.loads(json_string)

        obj_prim = Serializable.deserialize_prim(json_dict["_obj_type"])
        player_id_prim = Serializable.deserialize_prim(json_dict["_player_id"])

        return MapObject(obj_type=obj_prim, player_id=player_id_prim)
