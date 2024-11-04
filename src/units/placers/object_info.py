"""
TODO: Add module description.
"""

from aoe2mapgenerator.src.common.enums.enum import ObjectSize
from AoE2ScenarioParser.datasets.support.info_dataset_base import InfoDatasetBase
from aoe2mapgenerator.src.common.types import AOE2ObjectType


class ObjectInfo:
    """
    Class for the Age of Empires 2 Object Information.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_object_width(aoe2_object: AOE2ObjectType):
        """
        Returns the effective width of an object.
        """
        if not isinstance(aoe2_object, InfoDatasetBase):
            return 1

        return ObjectSize(aoe2_object._name_).value

    @staticmethod
    def get_object_height(aoe2_object: AOE2ObjectType):
        """
        Returns the effective height of an object.
        """
        if not isinstance(aoe2_object, InfoDatasetBase):
            return 1

        return ObjectSize(aoe2_object._name_).value

    @staticmethod
    def get_object_size(aoe2_object: AOE2ObjectType):
        """
        Returns the effective size of an object.
        """
        if not isinstance(aoe2_object, InfoDatasetBase):
            return 1

        return ObjectSize(aoe2_object._name_).value

    @staticmethod
    def get_object_effective_width(aoe2_object: AOE2ObjectType, margin: int = 0):
        """
        Returns the effective width of an object.
        """
        if not isinstance(aoe2_object, InfoDatasetBase):
            return 1

        return ObjectSize(aoe2_object._name_).value + margin

    @staticmethod
    def get_object_effective_height(aoe2_object: AOE2ObjectType, margin: int = 0):
        """
        Returns the effective height of an object.
        """
        if not isinstance(aoe2_object, InfoDatasetBase):
            return 1

        return ObjectSize(aoe2_object._name_).value + margin

    @staticmethod
    def get_object_effective_size(aoe2_object: AOE2ObjectType, margin: int = 0):
        """
        Returns the effective size of an object.
        """
        if not isinstance(aoe2_object, InfoDatasetBase):
            return 1

        return ObjectSize(aoe2_object._name_).value + margin
