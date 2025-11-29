"""
Templates package initialization.
Import all template modules here to ensure they are registered with the template manager.
"""

# Import template manager and decorator
from src.templates.template_decorator import register_template, get_template_manager
from src.templates.template_types import TemplateType
from src.templates.abstract_template import AbstractTemplate

# Import all template implementations to register them
from src.templates.fort import FortTemplate
from src.templates.decor import OakForestTemplate, SnowForestTemplate
# Import other template modules as needed

# Make the template manager accessible
template_manager = get_template_manager()