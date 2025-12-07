"""
Template class for placing objects on a map.
"""
from typing import Dict, Callable, Any, List, Optional, Type, Union, Tuple, TYPE_CHECKING
from dataclasses import dataclass

from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.units import UnitInfo


@dataclass
class TemplateConfig:
    """Configuration parameters for a template"""
    point_collection: PointCollection
    center_point: Tuple[int, int] = (50, 50)
    size: int = 20
    player_id: PlayerId = PlayerId.ONE
    gate_type: GateType = GateType.FORTIFIED_GATE
    # Add more configurable parameters as needed


class TemplateManager:
    """
    Class for managing and applying templates.
    """

    def __init__(self) -> None:
        self.templates: Dict[TemplateType, Type[AbstractTemplate]] = {}
    
    def register_template(self, template_type: TemplateType, template_class: Type[AbstractTemplate]) -> None:
        """
        Register a template with the manager.
        
        Args:
            template_type: Enum value to identify the template
            template_class: The template class that implements AbstractTemplate
        """
        self.templates[template_type] = template_class
    
    def apply_template(self, 
                      map_manager: IMapManager, 
                      point_collection: PointCollection,
                      template_type: TemplateType, 
                      config: Optional[TemplateConfig] = None, 
                      **kwargs) -> None:
        """
        Apply a template to the map.
        
        Args:
            template_type: Enum value of the template to apply
            map_manager: The map manager object
            point_collection: Collection of points to work with
            config: Optional configuration parameters for the template
            **kwargs: Additional parameters to pass to the template
        """
        if template_type not in self.templates:
            raise ValueError(f"Template '{template_type.name}' not found")
        
        template_class = self.templates[template_type]
        
        # Combine config and kwargs
        all_kwargs = {}
        if config:
            all_kwargs = {
                'center_point': config.center_point,
                'player_id': config.player_id,
                'size': config.size,
                'gate_type': config.gate_type,
                # Add more parameters as needed
            }
        
        # Override with any explicit kwargs
        all_kwargs.update(kwargs)
        
        # Generate the template
        template_class.generate(map_manager, point_collection, **all_kwargs)
