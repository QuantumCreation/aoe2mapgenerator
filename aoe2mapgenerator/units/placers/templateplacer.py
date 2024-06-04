import ast
import inspect
import os
from copy import deepcopy
from difflib import SequenceMatcher
from time import time
from typing import Union

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo
from yaml import UnsafeLoader, load

from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_PLAYER,
    TEMPLATE_DIR_LINUX,
)
from aoe2mapgenerator.common.enums.enum import MapLayerType, YamlReplacementKeywords


# May replace or add separate support for json
# For now, yaml is the easiest
class TemplatePlacerMixin:
    """
    Handles placing templates.
    """

    def _load_yaml(
        self, template_file_name: str, base_template_dir: str = TEMPLATE_DIR_LINUX
    ) -> dict:
        """
        Loads yaml file form the template file name.

        Information:
        Saves loaded yaml file so future calls are faster.

        Args:
            template_file_name: Name of the template file.
            base_template_dir: Base directory of the template file.

        Returns:
            dict: Loaded yaml file.

        Example:
            >>> load_yaml("test.yaml")
            {'command_list': [{'command_name': 'place_template', 'parameters': {'template_file_name': 'test2.yaml'}}]}
        """
        if template_file_name in self.template_names:
            return deepcopy(self.template_names[template_file_name])
        else:
            print(f"NEW TEMPLATE LOADED: {template_file_name}")
            with open(os.path.join(base_template_dir, template_file_name), "r") as f:
                yaml = load(f, Loader=UnsafeLoader)
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
        if "base_template_dir" not in kwargs:
            kwargs["base_template_dir"] = TEMPLATE_DIR_LINUX

        template = self._load_yaml(template_file_name, kwargs["base_template_dir"])

        _validate_user_included_required_fields(template, kwargs["map_layer_type_list"])

        symbol_table = {}

        symbol_table = _create_initial_symbol_table(**kwargs)

        for command in template["command_list"]:

            self.call_function(
                function_name=command["command_name"],
                parameters=command["parameters"],
                symbol_table=symbol_table,
            )

    def call_function(
        self,
        function_name: str,
        parameters: dict,
        symbol_table: dict = {},
    ):
        """
        Calls a function with the given arguments.

        Args:
            function_name: Name of the function to call.
            parameters: Key word arguments to pass to the function.
            symbol_table: Dictionary mapping yaml substitution variables to python objects.

        Example:
            Parameters are mapped with the key being the name of the parameter, and the value
            being the specific argument to pass to the function for that parameter.
        """
        function = getattr(self, function_name)

        _validate_user_kwarg_input(function, parameters)
        _convert_parameters_to_python_data_types(parameters, symbol_table)

        # Calls the function with the final parameters
        function(**parameters)


# -------------------------------- Conversion Functions ------------------------------


def _convert_array_space_type(array_space_type: list, dictionary: dict) -> None:
    """
    Converts a yaml array space type list into python objects.

    Args:
        array_space_type_list (list): List of array space types.
        dictionary (dict): Dictionary mapping yaml substitution variables to python objects.
    """

    if type(array_space_type) == list:
        if len(array_space_type) != 2:
            raise ValueError(
                f"Array space types must have a length of 2, not {len(array_space_type)}."
            )
        array_space_type[0] = _string_to_aoe2_enum_type(array_space_type[0])

        if array_space_type[1] in dictionary:
            return (array_space_type[0], dictionary[array_space_type[1]])
        if array_space_type[1] is None:
            return (array_space_type[0], DEFAULT_PLAYER)
        return PlayerId[array_space_type[1]]
    elif array_space_type in dictionary:
        return dictionary[array_space_type]
    elif type(array_space_type) == int:
        return array_space_type

    raise ValueError(f"The array space type '{array_space_type}' is not valid.")


# Would a dataclass somehow be useful here? Maybe include separate YAML format verifier.
# Also, this ugly sonofabitch function needs some work. We'll shall attend to his needs soon.
# Also converts from the variable names of types into actual types
def _convert_parameters_to_python_data_types(parameters, symbol_table):
    """
    Takes the yaml input and turns it into python objects.

    Args:
        ...
    """
    for parameter in parameters:
        # print(parameter)
        parameters[parameter] = _convert_parameter_to_python_type(
            parameter, parameters[parameter], symbol_table
        )


def _convert_parameter_to_python_type(
    parameter_type: str,
    parameter_value: Union[str, int, list],
    symbol_table: dict,
) -> Union[None, int, float, str]:
    """
    Converts a string to a python type. Uses the symbol table to replace variables as needed.

    Args:
        value (str): String to convert.

    Returns:
        Union[None, int, float, str]: Converted value.
    """
    # Return current value if the value is already a python type

    # This code makes it so that the top level is a list, and the lower levels are tuples
    # This makes it cover differnet cases, but it is liable to break things later

    if parameter_value is None:
        return None

    try:
        val = ast.literal_eval(parameter_value)
        return val
    except:
        pass

    if type(parameter_value) in [int, float, bool]:
        return parameter_value

    if (
        type(parameter_value) == str
        and len(parameter_value) > 0
        and parameter_value[0] == "$"
    ):
        if parameter_value not in symbol_table:
            raise ValueError(
                f"The value '{parameter_value}' is not a valid substitution variable."
            )

        return symbol_table[parameter_value]

    if type(parameter_value) == list:
        if parameter_type == "array_space_type_list":
            result = [
                _convert_parameter_to_python_type(None, item, symbol_table)
                for item in parameter_value
            ]
            result = [tuple(item) for item in result]
            return result

        return [
            _convert_parameter_to_python_type(parameter_type, item, symbol_table)
            for item in parameter_value
        ]

    if parameter_value.count(".") == 1:
        return _convert_value_to_enum(parameter_value)

    print(f"None was returned for the parameter: {parameter_value}")
    # print(parameter_value.count('.'))
    return None


def _convert_string_string_tuple_to_enum_player_tuple(
    string_tuple: tuple,
) -> Union[None, int, float, str]:
    """
    Converts a string string tuple to an enum player tuple.

    Args:
        string_tuple (tuple): String string tuple.

    Returns:
        tuple: Enum player tuple.
    """
    object = _convert_value_to_enum(string_tuple[0])
    playerId = (
        PlayerId.GAIA
        if string_tuple[1] is None
        else _convert_value_to_enum(string_tuple[1])
    )
    return (object, playerId)


def _create_initial_symbol_table(**kwargs) -> dict:
    """
    Creates an initial symbol table for the yaml file.

    Args:
        ...

    Returns: A dictionary mapping from yaml substitution variables to python objects.
    """
    # Maybe add more fields later and organize better
    symbol_table = dict()

    if "map_layer_type_list" in kwargs:
        for map_layer_type in kwargs["map_layer_type_list"]:
            symbol_table[f"${map_layer_type._name_}_V"] = map_layer_type

    if "array_space_type_list" in kwargs:
        map_layer_type_list = kwargs["map_layer_type_list"]
        for i, array_space_type in enumerate(kwargs["array_space_type_list"]):
            symbol_table[f"${map_layer_type_list[i]._name_}"] = array_space_type

    if "player_id" in kwargs:
        if kwargs["player_id"] is not None:
            symbol_table[YamlReplacementKeywords.PLAYER_ID.value] = kwargs["player_id"]

    if "gate_type" in kwargs:
        symbol_table[YamlReplacementKeywords.GATE_TYPE.value] = kwargs["gate_type"]

    return symbol_table


# Maybe add more fields later and organize better
def _validate_user_included_required_fields(
    template: dict,
    map_layer_type_list: list,
):
    """
    Validates the input to the placement function.

    Args:
        template: Loaded yaml template.
        map_layer_type_list:
    """
    required_inputs = [MapLayerType[text] for text in template["required_inputs"]]

    for input in required_inputs:
        if input not in map_layer_type_list:
            raise ValueError(f"The template requires the {input} field.")

    return True


# Could also check that required args 100% included. I'll deal with this laters. Bro.
def _validate_user_kwarg_input(function, parameters) -> None:
    """
    Validates that the key word arguments received match the keywords of the function.

    Args:
        function (function): The function to validate.
        parameters (dict): The key word arguments to validate.
    """
    # Not all of these arguments need to be included, but if an argument not matching these keywords is given.
    # The user has made a mistake.
    arg_spec = inspect.getfullargspec(function)
    acceptable_args = arg_spec.args
    required_args = arg_spec.args[
        : -(0 if arg_spec.defaults is None else len(arg_spec.defaults))
    ]

    # I THINK SOMETHING IS WRONG HERE. CHECK IF THE REQUIRED ARGS ARE CHECKED CORRECTLY.
    if len(required_args) > 0 and required_args[0] == "self":
        required_args.remove("self")

    for arg in required_args:
        if arg not in parameters:
            closest_match = max(
                list(parameters),
                key=lambda key_word_arg: SequenceMatcher(
                    None, arg.lower(), key_word_arg.lower()
                ).ratio(),
            )

            raise ValueError(
                f"The required key word argument '{arg}' was not included. "
                f"You wrote '{closest_match}', did you mean '{arg}'?"
            )

    # If the function accepts keyword arguments, we don't know what acceptable args are, hence skip.
    if arg_spec.varkw is None:
        for key_word_arg in parameters:
            if key_word_arg not in acceptable_args:
                closest_match = max(
                    acceptable_args,
                    key=lambda acc_arg: SequenceMatcher(
                        None, key_word_arg.lower(), acc_arg.lower()
                    ).ratio(),
                )

                raise ValueError(
                    f"The key word argument '{key_word_arg}' for the function '{function.__name__}' was invalid. "
                    f"You wrote '{key_word_arg}', did you mean '{closest_match}'?"
                )

    # Do error handling later


def _string_to_aoe2_enum_type(text, default_value=None, return_default=False):
    """
    Converts a string to an age of empires enum type.

    Args:
        text: Input corresponding to an enum type.
        default_value: Value to default to.
        return_default: Boolean declaring whether or not to use a default.
    """
    AOE2_enums = [PlayerId, UnitInfo, BuildingInfo, OtherInfo, TerrainId]

    # LMAO
    for enum in AOE2_enums:
        try:
            return enum[text]
        except:
            continue

    if return_default:
        return default_value

    raise ValueError(f"The value '{text}' was not found in any existing enum.")


def _convert_value_to_enum(string: str) -> Union[None, int, float, str]:
    """
    Converts a string to an enum type.

    Args:
        string (str): The string to convert in the form Enum.type.

    Returns:
        Union[None, int, float, str]: _description_
    """

    try:
        enum_type, enum_value = string.split(".")
    except:
        raise ValueError(
            f"The value '{string}' of type '{type(string)}'is not a valid enum type."
        )

    try:
        return globals()[enum_type][enum_value]
    except:
        raise ValueError(
            f"No enum type '{enum_type}' with value '{enum_value}' was found."
        )
