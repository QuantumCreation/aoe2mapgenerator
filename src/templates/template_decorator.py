"""
Decorator functions for template registration.
"""
from src.templates.template_types import TemplateType
from src.templates.templates_manager import TemplateManager

# Global template manager instance
_TEMPLATE_MANAGER = TemplateManager()

def register_template(template_type: TemplateType):
    """
    Decorator to register a template class with the template manager.
    
    Args:
        template_type: Enum value to identify the template
        
    Returns:
        The decorated class
    """
    def decorator(template_class):
        _TEMPLATE_MANAGER.register_template(template_type, template_class)
        return template_class
    return decorator

def get_template_manager() -> TemplateManager:
    """Get the global template manager with all registered templates"""
    return _TEMPLATE_MANAGER