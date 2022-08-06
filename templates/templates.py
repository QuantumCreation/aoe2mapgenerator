from common.enums.enum import TemplateTypes
from abc import ABC, abstractmethod
# from units.placers.templateplacer import 

class AbstractTemplate():
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
    def terrain_placement(self):
        """
        TODO
        """
    
    @abstractmethod
    def object_placement(self):
        """ 
        TODO
        """

class TemplateHandler():
    """
    TODO
    """

    # UNSURE HOW THIS SHOULD WORK
    def __init__(self):
        """
        TODO
        """

    def place_template(self, template: AbstractTemplate):
        """
        TODO
        """
    
    # ------------------- HELPER METHODS --------------------

    def _check_placement(self):
        """
        TODO
        """

    def _place(self):
        """
        TODO
        """
    
    def _check_and_place(self):
        """
        TODO
        """
