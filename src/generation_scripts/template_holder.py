"""
Template Holder class which holders objects of the Template class.
"""

from aoe2mapgenerator.src.generation_scripts.template import AbstractTemplate


class TemplateHolder:
    """
    Holds the Template objects with generation functions.
    """

    def __init__(self):
        self.templates: list[AbstractTemplate] = []

    def get_templates(self):
        """
        Lists the templates.
        """
        return self.templates

    def load_templates_from_directory(self, directory: str):
        """
        Loads the templates from a directory.
        """
        pass

    def add_template(self, template: AbstractTemplate):
        """
        Adds a template to the list.
        """
        self.templates.append(template)
        return self

    def call_template(self, template: AbstractTemplate):
        """
        Calls the template.
        """
        template.generate()
        return self
