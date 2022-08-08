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
from time import time
from copy import deepcopy

# May replace or add separate support for json
# For now, yaml is the easiest
class TemplatePlacerMixin(PlacerMixin):
    """
    Handles placing templates.
    """

    def load_yaml(self, template_file_name: str):
        """
        TODO
        """
        if template_file_name in self.template_names:
            print("DEEPCOPY")
            return deepcopy(self.template_names[template_file_name])
        else:
            print("YAML LOADED")
            with open(os.path.join(BASE_TEMPLATE_DIR, template_file_name), 'r') as f:
                yaml = load(f, Loader = UnsafeLoader)
                self.template_names[template_file_name] = deepcopy(yaml)
                return yaml

    # Loading yaml files seems inefficient, look for better ways.
    # Maybe consider preloading the yaml so that new calls of the same
    # template doesn't repeat the loading process.
    def place_template(
        self,
        template_file_name: str,
        value_type_list: list[ValueType] = None,
        array_space_type_list: list[Union[int, tuple]] = None,
        obj_type_list: list = None,
        player_id: PlayerId = DEFAULT_PLAYER,
        ):
        """
        Places a template object.

        Args:
            template_file_name: Name of the template file to load.
            ...
        """
        start = time()
        template = self.load_yaml(template_file_name)
        end = time()
        print(f"Time to load yaml: {end-start}")

        self.validate_input(template, value_type_list)
        
        total_conversion = 0
        total_function_call = 0
        for command in template['command_list']:
            start = time()
            function = getattr(self, command['command_name'])
            self.convert_yaml_command_to_python_data_types(
                command = command['parameters'],
                value_type_list = value_type_list,
                array_space_type_list = array_space_type_list,
                obj_type_list = obj_type_list,
                player_id = player_id,
                )
            end = time()
            total_conversion += end-start
            start = time()
            function(**command['parameters'])
            end = time()
            total_function_call += end-start
        print(f"Time to convert yaml to python: {total_conversion}")
        print(f"Time to run python functions: {total_function_call}")
    
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

        Args:
            ...
        """
        dictionary = self.create_dictionary_mapping(
            value_type_list,
            array_space_type_list,
            obj_type_list,
            player_id,
            )
        
        command['value_type_list'] = [
            dictionary[value] if value in dictionary 
            else ValueType(value) 
            for value in command['value_type_list']]
        
        # This is bad
        
        command['array_space_type_list'] = [
                dictionary[value] if type(value) == str and value in dictionary
                else
                (
                self.string_to_aoe2_enum_type(value[0]),
                DEFAULT_PLAYER if value[1] is None else PlayerId[value[1]]
                )
                if len(value) == 2 else value
                for value in command['array_space_type_list']
            ]

        command['obj_type_list'] = [
            dictionary[value] if value in dictionary
            else self.string_to_aoe2_enum_type(value)
            for value in command['obj_type_list']
        ]

        command['player_id'] = (
            dictionary[command['player_id']] if command['player_id'] in dictionary 
            else (PlayerId(command['player_id']) if command['player_id'] is not None
                else DEFAULT_PLAYER
                )
            )

        # IDK LOL
        command['clumping_func'] = command['clumping_func']
        command['start_point'] = tuple(command['start_point'])

    
    # Do error handling later
    def string_to_aoe2_enum_type(self, text, default_value = None, return_default = False):
        """
        Converts a string to an age of empires enum type.

        Args:

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
        Creates a dictionary mapping from placeholder vars to python objects.

        Args:

        """
        default_dict = {}

        # String formatted should probably be optimized/made pretty/use enum. SEE ENUMS.
        for value_type in value_type_list:
            default_dict[f"${value_type._name_}_V"] = value_type
        
        for i, array_space_type in enumerate(array_space_type_list):
            default_dict[f"${value_type_list[i]._name_}_A"] = array_space_type
        
        # OBJ LIST NOT YET SUPPORTED

        if player_id is not None:
            default_dict[YamlReplacementKeywords.PLAYER_ID.value] = player_id

        return default_dict

    def validate_input(self,
        template,
        value_type_list,
        ):
        """
        Validates the input to the placement function.

        Args:
            template: Loaded yaml template.
            value_type_list: 
        """
        required_inputs = [ValueType[text] for text in template['required_inputs']]

        for input in required_inputs:
            if input not in value_type_list:
                raise ValueError(f"The template requires the {input} field.")

        return True