"""
This file contains the base class for all the generation scripts.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from AoE2ScenarioParser.datasets.players import PlayerId
from aoe2mapgenerator.map.imap_manager import IMapManager


class AbstractTemplate(ABC):
    """
    Base class for all generation scripts.
    """

    @abstractmethod
    def __init__(self, name: str, description: str):
        """
        Initialize the template.
        
        Args:
            name: Name of the template
            description: Description of what the template does
        """
        pass

    @staticmethod
    @abstractmethod
    def generate(
        map_manager: IMapManager, 
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.ONE,
        **kwargs
    ) -> PointCollection:
        """
        Generate the template on the map.
        
        Args:
            map_manager: The map manager instance
            point_collection: Collection of points to work with
            center_point: Center coordinates for the template
            size: Size/scale of the template
            player_id: Player who owns the generated objects
            **kwargs: Additional template-specific parameters
        """
        pass
