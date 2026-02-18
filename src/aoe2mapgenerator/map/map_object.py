"""
TODO: Add module description
"""

from typing import Any
from dataclasses import dataclass
from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    DisplacementType,
)

from aoe2mapgenerator.serializer.base_serializer import Serializable
import ujson as json


@dataclass(frozen=True)
class MapObject:
    """
    Class for the Age of Empires Map Object
    """
    obj_type: AOE2ObjectType | DisplacementType = DEFAULT_EMPTY_VALUE
    player_id: PlayerId = PlayerId.GAIA

    def __repr__(self):
        return f"MapObject({self.obj_type}, Player: {self.player_id})"

    def __hash__(self):
        return hash((self.obj_type, self.player_id))

    def get_obj_type(self) -> AOE2ObjectType | DisplacementType:
        """
        Gets the object type.
        """
        return self.obj_type

    def get_player_id(self) -> PlayerId:
        """
        Gets the player id.
        """
        return self.player_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "_type": self.__class__.__name__,
            "_obj_type": Serializable.serialize_prim(self.obj_type),
            "_player_id": Serializable.serialize_prim(self.player_id),
        }

    def serialize(self) -> str:
        """Legacy serialization for backwards compatibility."""
        data: dict[str, Any] = self.to_dict()
        return json.dumps(data)

    def model_dump_json(self) -> str:
        """Pydantic-style JSON serialization."""
        return json.dumps({
            "obj_type": Serializable.serialize_prim(self.obj_type),
            "player_id": Serializable.serialize_prim(self.player_id),
        })
    
    def model_dump(self) -> dict[str, Any]:
        """Pydantic-style dict serialization."""
        return {
            "obj_type": Serializable.serialize_prim(self.obj_type),
            "player_id": Serializable.serialize_prim(self.player_id),
        }

    @staticmethod
    def deserialize(json_string: str | dict[str, Any]) -> "MapObject":
        """Legacy deserialization for backwards compatibility."""
        json_dict: dict[str, Any]
        if isinstance(json_string, dict):
            json_dict = json_string
        else:
            json_dict = json.loads(json_string)

        obj_prim = Serializable.deserialize_prim(json_dict["_obj_type"])
        player_id_prim = Serializable.deserialize_prim(json_dict["_player_id"])

        return MapObject(obj_prim, player_id_prim)
    
    @staticmethod
    def model_validate_json(json_string: str) -> "MapObject":
        """Pydantic-style JSON deserialization."""
        json_dict = json.loads(json_string)
        obj_type = Serializable.deserialize_prim(json_dict["obj_type"])
        player_id = Serializable.deserialize_prim(json_dict["player_id"])
        return MapObject(obj_type, player_id)
