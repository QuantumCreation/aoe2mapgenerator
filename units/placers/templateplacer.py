import random
from re import A
from site import abs_paths
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize, ValueType
from AoE2ScenarioParser.datasets.players import PlayerId
from units.placers.objectplacer import PlacerMixin
from templates.abstract_template import AbstractTemplate
from common.constants.constants import BASE_TEMPLATE_DIR

from typing import Union
from yaml import load, UnsafeLoader
import os


class TemplatePlacerMixin(PlacerMixin):
    """
    TODO
    """

    def place_template(
        self,
        template_file_name: str,
        value_types: list[ValueType],
        array_space_types: list[Union[int, tuple]],
        ):
        """
        TODO
        """
        with open(os.path.join(BASE_TEMPLATE_DIR, template_file_name), 'r') as f:
            template = load(f, Loader = UnsafeLoader)

            for command_dict in template['command_list']:
                func = getattr(PlacerMixin, command_dict['function_name'])
                self.func(**command_dict)