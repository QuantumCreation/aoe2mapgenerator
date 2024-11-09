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

    def generate(self, point_collection: PointCollection, map_manager: MapManager):
        """
        Generates a village
        """
