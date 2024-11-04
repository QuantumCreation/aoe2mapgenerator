from enum import Enum
from aoe2mapgenerator.src.common.enums.enum import *
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId


def serialize_enum(enum_instance: Enum) -> str:
    """
    Converts an enum instance to a string.

    Args:
        enum_instance (Enum): Enum instance to convert to string.

    Returns:
        str: String representation of the enum instance.
    """
    try:
        instance_name = enum_instance.name
        enum_name = enum_instance.__class__.__name__
    except:
        raise ValueError("Error parsing enum instance")

    return f"{enum_name}.{instance_name}"


def deserialize_enum(enum_string: str) -> Enum:
    """
        Deserializes an enum.
    def serialize_enum():

        Args:
            enum_instance (Enum): Enum instance to convert to string.

        Returns:
            str: String representation of the enum instance.
    """
    try:
        enum_name, instance_name = enum_string.split(".")
    except:
        raise ValueError("Error parsing enum string")

    try:
        enum = globals()[enum_name]
    except:
        try:
            enum = locals()[enum_name]
        except:
            raise ValueError(f"Error parsing enum string: {enum_string}")

    return enum[instance_name]
