"""
Templates package initialization.
Import all template modules here to ensure they are registered with the template manager.
"""

# Import template manager and decorator
from aoe2mapgenerator.templates.template_decorator import register_template, get_template_manager
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate

# Import all template implementations to register them
from aoe2mapgenerator.templates.city_hybrid import CityTemplate
from aoe2mapgenerator.templates.fort import FortTemplate
from aoe2mapgenerator.templates.palace import PalaceTemplate
from aoe2mapgenerator.templates.decor import OakForestTemplate, SnowForestTemplate

# Nature / biome templates (pond, river, forests, biomes)
from aoe2mapgenerator.templates.nature import (
    PondTemplate,
    RiverSegmentTemplate,
    PineForestTemplate,
    WinterLandscapeTemplate,
    DesertTemplate,
    DesertOasisTemplate,
    SavannahTemplate,
    RainforestTemplate,
    MediterraneanTemplate,
)

# Make the template manager accessible
template_manager = get_template_manager()
