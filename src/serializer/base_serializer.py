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
from typing import Any, Dict, List, Callable, Type, get_type_hints
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial


# region Function Serialization
class Serializable(ABC):

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


class SerializationRegistry:
    """Registry for serializable types"""

    def __init__(self):
        self._types: Dict[str, Type[Serializable]] = {}

    def register_type(self, cls: Type[Serializable]) -> None:
        """Register a serializable type"""
        if not issubclass(cls, Serializable):
            raise ValueError(f"Class {cls.__name__} must inherit from Serializable")
        self._types[cls.__name__] = cls

    def deserialize_value(self, data: Dict[str, Any]) -> Serializable:
        """Deserialize a dictionary into an object"""
        if "_type" not in data:
            raise ValueError("Serialized data missing '_type' field")

        type_name = data["_type"]
        if type_name not in self._types:
            raise ValueError(f"Unknown type: {type_name}")

        return self._types[type_name].deserialize(data)


class FunctionRunner:
    """
    A class that executes functions based on JSON configuration,
    with support for custom serializable objects.
    """

    def __init__(self):
        self._function_registry: Dict[str, Callable] = {}
        self._serialization_registry = SerializationRegistry()

    def register_function(self, name: str, func: Callable) -> None:
        """Register a function with a given name"""
        self._function_registry[name] = func

    def register_serializable(self, cls: Type[Serializable]) -> None:
        """Register a serializable type"""
        self._serialization_registry.register_type(cls)

    def _deserialize_arg(self, value: Any, param_type: Type) -> Any:
        """
        Deserialize a single argument based on its type hint.
        Handles nested lists and dictionaries containing serializable objects.
        """
        if isinstance(value, dict) and "_type" in value:
            return self._serialization_registry.deserialize_value(value)

        if isinstance(value, list):
            # Handle List[SomeType] annotations
            if hasattr(param_type, "__origin__") and param_type.__origin__ is list:
                item_type = param_type.__args__[0]
                return [self._deserialize_arg(item, item_type) for item in value]

        if isinstance(value, dict):
            # Handle Dict[str, SomeType] annotations
            if hasattr(param_type, "__origin__") and param_type.__origin__ is dict:
                key_type, value_type = param_type.__args__
                return {
                    key: self._deserialize_arg(val, value_type)
                    for key, val in value.items()
                }

        return value

    def _deserialize_args(
        self, func: Callable, args: List[Any], kwargs: Dict[str, Any]
    ) -> tuple[List[Any], Dict[str, Any]]:
        """Deserialize all arguments based on function type hints"""
        type_hints = get_type_hints(func)

        # Get parameter names in order
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        # Deserialize positional arguments
        deserialized_args = [
            self._deserialize_arg(arg, type_hints[param_names[i]])
            for i, arg in enumerate(args)
        ]

        # Deserialize keyword arguments
        deserialized_kwargs = {
            key: self._deserialize_arg(value, type_hints[key])
            for key, value in kwargs.items()
            if key in type_hints
        }

        return deserialized_args, deserialized_kwargs

    def execute_from_json(self, json_config: str) -> List[Any]:
        """
        Execute functions based on JSON configuration.
        Automatically deserializes arguments based on type hints.

        Expected JSON format:
        {
            "functions": [
                {
                    "name": "function_name",
                    "args": [...],
                    "kwargs": {...}
                }
            ]
        }
        """
        try:
            config = json.loads(json_config)
            results = []

            for func_config in config["functions"]:
                name = func_config["name"]
                args = func_config.get("args", [])
                kwargs = func_config.get("kwargs", {})

                if name not in self._function_registry:
                    raise ValueError(f"Function '{name}' not found in registry")

                func = self._function_registry[name]
                deserialized_args, deserialized_kwargs = self._deserialize_args(
                    func, args, kwargs
                )

                result = func(*deserialized_args, **deserialized_kwargs)
                results.append(result)

            return results

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except KeyError as e:
            raise ValueError(f"Missing required key in JSON: {str(e)}")
