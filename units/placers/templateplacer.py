from dataclasses import dataclass
import random
from re import A
from site import abs_paths
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize, MapLayerType, GateTypes
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from units.placers.objectplacer import PlacerMixin
from common.constants.constants import BASE_TEMPLATE_DIR, DEFAULT_PLAYER
import re
from typing import Union
from yaml import load, UnsafeLoader
import os
from common.enums.enum import YamlReplacementKeywords
from time import time
from copy import deepcopy
import inspect
from difflib import SequenceMatcher

# May replace or add separate support for json
# For now, yaml is the easiest
class TemplatePlacerMixin(PlacerMixin):
    """
    Handles placing templates.
    """

    def load_yaml(self, template_file_name: str):
        """
        Loads yaml file form the template file name. 

        Information:
        Saves loaded yaml file so future calls are faster.

        Args:
            template_file_name: Name of the template file.
        """
        if template_file_name in self.template_names:
            return deepcopy(self.template_names[template_file_name])
        else:
            print(f"NEW TEMPLATE LOADED: {template_file_name}")
            with open(os.path.join(BASE_TEMPLATE_DIR, template_file_name), 'r') as f:
                yaml = load(f, Loader = UnsafeLoader)
                self.template_names[template_file_name] = deepcopy(yaml)
                return yaml

    # Also consider finding a way to prevent infinite loops of place template
    # when one template calls another template.
    def place_template(
        self,
        template_file_name: str,
        **kwargs,
        ):
        """
        Places a template object.

        Args:
            template_file_name: Name of the template file to load.
            kwargs: Key word arguments corresponding to various placer variables.
        """
        # start = time()
        template = self.load_yaml(template_file_name)
        # end = time()
        # print(f"Time to load yaml: {end-start}")

        self._validate_user_included_required_yaml_fields(template, kwargs['map_layer_type_list'])
        
        total_conversion = 0
        total_function_call = 0

        calls = []

        for command in template['command_list']:
            # start = time()
            function = getattr(self, command['command_name'])
            self._validate_user_kwarg_input(function, **command['parameters'])
  
            self._convert_yaml_command_to_python_data_types(
                parameters = command['parameters'],
                **kwargs
                )
            # end = time()
            # total_conversion += end-start
            start = time()
            function(**command['parameters'])
            end = time()
            total_function_call += end-start

            calls += [[command['command_name'], command['parameters'], end-start]]
        if max(calls, key = lambda x: x[2])[2] > 0.5:
            print(f"Longest call: {max(calls, key = lambda x: x[2])}")
        # print(f"Time to convert yaml to python: {total_conversion}")
        # print(f"Time to run {template_file_name}: {total_function_call}")
    
    # Would a dataclass somehow be useful here? Maybe include separate YAML format verifier.
    # Also, this ugly sonofabitch function needs some work. We'll shall attend to his needs soon.
    def _convert_yaml_command_to_python_data_types(
        self, 
        parameters,
        **kwargs,
        ):
        """
        Takes the yaml input and turns it into python objects.

        Args:
            ...
        """
        dictionary = self._create_dictionary_mapping(**kwargs)
        # STUFF
        if 'map_layer_type_list' in parameters:
            parameters['map_layer_type_list'] = [
                dictionary[value] if value in dictionary 
                else MapLayerType(value) 
                for value in parameters['map_layer_type_list']]
            
        # Maybe have the function handle the entire list to limit function calls?
        if 'array_space_type_list' in parameters:
            parameters['array_space_type_list'] = [
                    self.convert_array_space_type(value, dictionary)
                    for value in parameters['array_space_type_list']
                ]

        if 'obj_type_list' in parameters:
            parameters['obj_type_list'] = [
                dictionary[value] if value in dictionary
                else self.string_to_aoe2_enum_type(value)
                for value in parameters['obj_type_list']
            ]

        # GOD THIS TOOK SO LONG TO FIND. MAYBE CONVERT ADD BORDERS TO AN OBJECT TYPE LIST AS WELL.
        if 'obj_type' in parameters:
            parameters['obj_type'] = (
                dictionary[parameters['obj_type']] if parameters['obj_type'] in dictionary
                else self.string_to_aoe2_enum_type(parameters['obj_type'])
            )
            

        if 'player_id' in parameters:
            parameters['player_id'] = (
                dictionary[parameters['player_id']] if parameters['player_id'] in dictionary 
                else (PlayerId(parameters['player_id']) if parameters['player_id'] is not None
                    else DEFAULT_PLAYER
                    )
                )

        if 'gate_type' in parameters:
            parameters['gate_type'] = GateTypes(parameters['gate_type'])

        # IDK LOL
        if 'clumping_func' in parameters:
            parameters['clumping_func'] = parameters['clumping_func']
        
        if 'start_point' in parameters:
            parameters['start_point'] = tuple(parameters['start_point'])

    
    # Do error handling later
    def string_to_aoe2_enum_type(self, text, default_value = None, return_default = False):
        """
        Converts a string to an age of empires enum type.

        Args:
            text: Input corresponding to an enum type.
            default_value: Value to default to.
            return_default: Boolean declaring whether or not to use a default.
        """
        AOE2_enums = [PlayerId, UnitInfo, BuildingInfo, OtherInfo, TerrainId]

        for enum in AOE2_enums:
            try:
                return enum[text]
            except:
                continue

        if return_default:
            return default_value

        raise ValueError(f"The value \'{text}\' was not found in any existing enum.")
    
    def _create_dictionary_mapping(
        self,
        **kwargs,
        ):
        """
        Creates a dictionary mapping from placeholder variables to python objects.

        Args:

        """
        default_dict = {}

        # String formatted should probably be optimized/made pretty/use enum. SEE ENUMS.
        # IS THIS EVEN NECESSARY? WE WILL ALWAYS GET THE SAME MAPPING. WHY HAVE AN EXTRA VARIABLE FOR THIS?
        if 'map_layer_type_list' in kwargs:
            for map_layer_type in kwargs['map_layer_type_list']:
                default_dict[f"${map_layer_type._name_}_V"] = map_layer_type

        if 'array_space_type_list' in kwargs:
            map_layer_type_list = kwargs['map_layer_type_list']
            for i, array_space_type in enumerate(kwargs['array_space_type_list']):
                default_dict[f"${map_layer_type_list[i]._name_}"] = array_space_type

        # OBJ LIST NOT YET SUPPORTED

        if 'player_id' in kwargs:
            if kwargs['player_id'] is not None:
                default_dict[YamlReplacementKeywords.PLAYER_ID.value] = kwargs['player_id']

        if 'gate_type' in kwargs:
            default_dict[YamlReplacementKeywords.GATE_TYPE] = kwargs['gate_type']

        return default_dict

    # Maybe add more fields later and organize better
    def _validate_user_included_required_yaml_fields(self,
        template,
        map_layer_type_list,
        ):
        """
        Validates the input to the placement function.

        Args:
            template: Loaded yaml template.
            map_layer_type_list: 
        """
        required_inputs = [MapLayerType[text] for text in template['required_inputs']]

        for input in required_inputs:
            if input not in map_layer_type_list:
                raise ValueError(f"The template requires the {input} field.")

        return True

    # Could also check that required args 100% included. I'll deal with this laters. Bro.
    def _validate_user_kwarg_input(self, function, **kwargs):
        """
        Validates that the key word arguments received match the keywords of the function.

        Args:
            function: A function object.
            kwargs: The key word arguments received by the user.
        """
        # Not all of these arguments need to be included, but if an argument not matching these keywords is given.
        # The user has made a mistake.
        arg_spec = inspect.getfullargspec(function)
        acceptable_args = arg_spec.args
        required_args = arg_spec.args[:-(0 if arg_spec.defaults is None else len(arg_spec.defaults))]

        # I THINK SOMETHING IS WRONG HERE. CHECK IF THE REQUIRED ARGS ARE CHECKED CORRECTLY.
        if len(required_args) > 0 and required_args[0] == 'self':
            required_args.remove('self')

        for arg in required_args:
            if arg not in kwargs:
                closest_match = max(kwargs, key = lambda key_word_arg: SequenceMatcher(None,arg.lower(),key_word_arg.lower()).ratio())

                raise ValueError(
                    f"The required key word argument \'{arg}\' was not included. "
                    f"You wrote \'{closest_match}\', did you mean \'{arg}\'?"
                )

        # If the function accepts keyword arguments, we don't know what acceptable args are, hence skip.
        if arg_spec.varkw is None:
            for key_word_arg in kwargs:
                if key_word_arg not in acceptable_args:
                    closest_match = max(acceptable_args, key = lambda acc_arg: SequenceMatcher(None,key_word_arg.lower(),acc_arg.lower()).ratio())

                    raise ValueError(
                        f"The key word argument \'{key_word_arg}\' for the function \'{function.__name__}\' was invalid. "
                        f"You wrote \'{key_word_arg}\', did you mean \'{closest_match}\'?"
                        )

# -------------------------------- Conversion Functions ------------------------------

    def convert_array_space_type(self, array_space_type, dictionary):
        """
        Converts a yaml array space type list into python objects.

        Args:
            array_space_type_list: List of array space objects.
            dictionary: Dictionary mapping yaml substitution variables to python objects.
        """

        if type(array_space_type) == list:
            if len(array_space_type) != 2:
                raise ValueError(f"Array space types must have a length of 2, not {len(array_space_type)}.")
            array_space_type[0] = self.string_to_aoe2_enum_type(array_space_type[0])

            if array_space_type[1] in dictionary:
                return (array_space_type[0], dictionary[array_space_type[1]])
            if array_space_type[1] is None:
                return (array_space_type[0], DEFAULT_PLAYER)
            return PlayerId[array_space_type[1]]
        elif array_space_type in dictionary:
            return dictionary[array_space_type]
        elif type(array_space_type) == int:
            return array_space_type

        raise ValueError(f"The array space type \'{array_space_type}\' is not valid.")
