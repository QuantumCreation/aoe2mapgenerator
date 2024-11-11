"""
Defines classes which places villages on the map
"""

from src.generation_scripts.template import AbstractTemplate
from src.map.map_manager import MapManager
from src.units.placers.point_management.point_manager import (
    PointCollection,
)


class Village(AbstractTemplate):
    """
    Class to generate villages on the map
    """

    @staticmethod
    def generate(map_manager: MapManager, point_collection: PointCollection) -> None:
        """
        Generates a village
        """
