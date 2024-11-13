from typing import Any
from enum import Enum
from abc import ABC, abstractmethod
from src.serializer.serialization_utils import (
    serialize_enum,
    deserialize_enum,
)
from src.common.enums.enum import *
from src.common.enums.enum import GateType
import ujson as json
from typing import Any, Dict, List, Callable, Type, get_type_hints
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial


from src.serializer.base_serializer import Serializable, SerializationRegistry


class SerializationManager:
    """
    Class for managing serialization of objects.
    """

    def __init__(self):
        self._registry = SerializationRegistry()

    def register_all(self) -> None:
        """
        Register all serializable types.
        """
        for cls in Serializable.__subclasses__():
            if not inspect.isabstract(cls):
                self.register_type(cls)  # type: ignore[type-abstract]

    def register_type(self, cls: Type[Serializable]) -> None:
        """
        Register a serializable type.
        """
        self._registry.register_type(cls)

    def serialize(self, obj: Serializable) -> str:
        """
        Serialize an object.
        """
        return obj.serialize()

    def deserialize(self, json_string: str | dict) -> Any:
        """
        Deserialize a string.
        """
        return self._registry.deserialize(json_string)
