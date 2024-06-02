
from aoe2mapgenerator.common.enums.enum import ObjectSize, AOE2Object
from AoE2ScenarioParser.datasets.players import PlayerId


class ObjectInfo:

    def __init__(self):
        pass
    
    @staticmethod
    def get_object_width(object: AOE2Object):
        """
        Returns the effective width of an object.
        """
        return ObjectSize(object._name_).value
    
    @staticmethod
    def get_object_height(object: AOE2Object):
        """
        Returns the effective height of an object.
        """
        return ObjectSize(object._name_).value
    
    @staticmethod
    def get_object_size(object: AOE2Object):
        """
        Returns the effective size of an object.
        """
        return ObjectSize(object._name_).value
    
    @staticmethod
    def get_object_effective_width(object: AOE2Object, margin: int = 0):
        """
        Returns the effective width of an object.
        """
        return ObjectSize(object._name_).value + margin
    
    @staticmethod
    def get_object_effective_height(object: AOE2Object, margin: int = 0):
        """
        Returns the effective height of an object.
        """
        return ObjectSize(object._name_).value + margin
    
    @staticmethod
    def get_object_effective_size(object: AOE2Object, margin: int = 0):
        """
        Returns the effective size of an object.
        """
        return ObjectSize(object._name_).value + margin