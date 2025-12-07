"""
Template Holder class which holders objects of the Template class.
"""

from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from typing import List


class TemplateHolder:
    """
    Holds the Template objects with generation functions.
    """

    def __init__(self) -> None:
        self.templates: List[AbstractTemplate] = []

    def get_templates(self) -> List[AbstractTemplate]:
        """
        Lists the templates.
        """
        return self.templates

    def load_templates_from_directory(self, directory: str) -> None:
        """
        Loads the templates from a directory.
        """
        pass

    def add_template(self, template: AbstractTemplate) -> "TemplateHolder":
        """
        Adds a template to the list.
        """
        self.templates.append(template)
        return self

    def call_template(self, template: AbstractTemplate) -> None:
        """
        Calls the template.
        """
        pass
