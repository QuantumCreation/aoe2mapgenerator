from dataclasses import dataclass
import random
from re import A
from site import abs_paths
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize, ValueType
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from units.placers.objectplacer import PlacerMixin
from templates.abstract_template import AbstractTemplate
from common.constants.constants import BASE_TEMPLATE_DIR, DEFAULT_PLAYER
import re
from typing import Union
from yaml import load, UnsafeLoader
import os
from common.enums.enum import YamlReplacementKeywords

# May replace or add separate support for json
# For now, yaml is the easiest
class TemplatePlacerMixin(PlacerMixin):
    """
    TODO
    """
    def place_template(
        self,
        template_file_name: str,
        value_type_list: list[ValueType] = None,
        array_space_type_list: list[Union[int, tuple]] = None,
        obj_type_list: list = None,
        player_id: PlayerId = DEFAULT_PLAYER,
        ):
        """
        TODO
        """
        with open(os.path.join(BASE_TEMPLATE_DIR, template_file_name), 'r') as f:
            template = load(f, Loader = UnsafeLoader)
            self.validate_input(template, value_type_list)

            for command in template['command_list']:
                function = getattr(self, command['command_name'])
                self.convert_yaml_command_to_python_data_types(
                    command = command['parameters'],
                    value_type_list = value_type_list,
                    array_space_type_list = array_space_type_list,
                    obj_type_list = obj_type_list,
                    player_id = player_id,
                    )
                function(**command['parameters'])
    
    # Would a dataclass somehow be useful here? Maybe include separate YAML format verifier.
    # Also, this ugly sonofabitch function needs some work. We'll shall attend to his needs soon.
    def convert_yaml_command_to_python_data_types(
        self, 
        command,
        value_type_list: list[ValueType] = None,
        array_space_type_list: list[Union[int, tuple]] = None,
        obj_type_list: list = None,
        player_id: PlayerId = DEFAULT_PLAYER,
        ):
        """
        Takes the yaml input and turns it into python objects.
        """

        if value_type_list is not None:
            command['value_type_list'] = value_type_list
        else:
            command['value_type_list'] = [ValueType(value) for value in command['value_type_list']]
        
        if array_space_type_list is not None:
            command['array_space_type_list'] = array_space_type_list
        else:
            command['array_space_type_list'] = [
                (
                self.string_to_aoe2_enum_type(value[0]),
                PlayerId[value[1]]
                ) 
                if type(value) == list else int(value) 
                for value in command['array_space_type_list']
            ]
        
        if obj_type_list is not None:
            command['obj_type_list'] = obj_type_list
        else:
            command['obj_type_list'] = [
                self.string_to_aoe2_enum_type(value)
                for value in command['obj_type_list']
            ]

        if player_id is not None:
            if command['player_id'] == YamlReplacementKeywords.PLAYER_ID.value:
                command['player_id'] = player_id
            else:
                command['player_id'] = DEFAULT_PLAYER
        else:
            try:
                command['player_id'] = PlayerId(command['player_id'])
            except:
                command['player_id'] = DEFAULT_PLAYER
        
        # IDK LOL
        command['clumping_func'] = command['clumping_func']
        command['start_point'] = tuple(command['start_point'])

    
    # Do error handling later
    def string_to_aoe2_enum_type(self, text, default_value = None, return_default = False):
        """
        TODO
        """
        AOE2_enums = [PlayerId, UnitInfo, BuildingInfo, OtherInfo, TerrainId]

        for enum in AOE2_enums:
            try:
                return enum[text]
            except:
                continue
        
        if return_default:
            return default_value
        
        raise ValueError("The value {text} was not found in any existing enum.")
    
    def create_dictionary_mapping(
        self,
        value_type_list: list[ValueType] = None,
        array_space_type_list: list[Union[int, tuple]] = None,
        obj_type_list: list = None,
        player_id: PlayerId = DEFAULT_PLAYER,
        ):
        """
        TODO
        """
        default_dict = {}

        # String formatted should probably be optimized/ made pretty.
        for value_type in value_type_list:
            default_dict[f"${value_type}"]

    def validate_input(self,
        template,
        value_type_list,
        ):
        """
        TODO
        """
        required_inputs = [ValueType[text] for text in template['required_inputs']]

        for input in required_inputs:
            if input not in value_type_list:
                raise ValueError(f"The template requires the {input} field.")

        return True