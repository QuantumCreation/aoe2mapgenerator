from common.enums.enum import TemplateTypes
from abc import ABC, abstractmethod
# from units.placers.templateplacer import 

class AbstractBaseTemplate():
    """
    TODO
    """

    def __init__(self, template_name: str, template_type: TemplateTypes, size = 1):
        """
        TODO
        """
        self.template_name = template_name
        self.template_type = template_type
        self.size = size
    
    # Currently doesn't differentiate walkable and unwalkable terrain.
    # Workaround is to place unwalkable terrain into the units map so that
    # You do not accidently place anything on top of it.

    @abstractmethod
    def initial_map_setup(self):
        """
        TODO
        """
    
    @abstractmethod
    def terrain_placement(self):
        """
        TODO
        """

    @abstractmethod
    def object_placement(self):
        """ 
        TODO
        """

    def list_place_template_commands(self):
        """
        TODO
        """
        self.initial_map_setup()
        self.terrain_placement()
        self.object_placement()
    

class AbstractTemplate(AbstractBaseTemplate):
    """
    TODO
    """
    
    def __init__(self, other_templates: dict[str, AbstractBaseTemplate]):
        """
        TODO
        """
        self.other_templates = other_templates
