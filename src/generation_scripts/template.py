"""
This file contains the base class for all the generation scripts.
"""

from abc import ABC, abstractmethod
from aoe2mapgenerator.src.map.map_manager import MapManager
from aoe2mapgenerator.src.units.placers.point_management.point_manager import (
    PointCollection,
)


class AbstractTemplate(ABC):
    """
    Base class for all generation scripts.
    """

    @abstractmethod
    def __init__(self, name: str, description: str):
        pass

    @staticmethod
    @abstractmethod
    def generate(point_collection: PointCollection, map_manager: MapManager):
        """
        Generate the map.
        """
        pass
