"""
Defines classes which places villages on the map
"""

from aoe2mapgenerator.src.generation_scripts.template import AbstractTemplate
from aoe2mapgenerator.src.map.map_manager import MapManager
from aoe2mapgenerator.src.units.placers.point_manager import PointManager


class Village(AbstractTemplate):
    """
    Class to generate villages on the map
    """

    def generate(self, point_manager: PointManager, map_manager: MapManager):
        """
        Generates a village
        """
