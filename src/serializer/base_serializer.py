from typing import Any
from enum import Enum
from abc import ABC, abstractmethod
from aoe2mapgenerator.src.serializer.serialization_utils import (
    serialize_enum,
    deserialize_enum,
)
from aoe2mapgenerator.src.common.enums.enum import *
from aoe2mapgenerator.src.common.enums.enum import GateType
import ujson as json


# region Function Serialization
class SerializableBase(ABC):

    @abstractmethod
    def serialize(self) -> Any:
        pass

    @staticmethod
    @abstractmethod
    def deserialize(json_string: str | dict) -> Any:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    def dump(self, dictionary: dict) -> str:
        return json.dumps(dictionary)

    @staticmethod
    def serialize_prim(primitive: Any) -> str:
        if isinstance(primitive, Enum):
            return serialize_enum(primitive)

        return json.dumps(primitive)

    @staticmethod
    def deserialize_prim(primitive_string: str) -> Any:
        try:
            return json.loads(primitive_string)
        except:
            return deserialize_enum(primitive_string)
