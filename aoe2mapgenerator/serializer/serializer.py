from aoe2mapgenerator.map.map import Map
import inspect
import json
from aoe2mapgenerator.common.enums.enum import MapLayerType
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.units.placers.templateplacer import _convert_value_to_enum
import json
from enum import Enum

def _get_functions(object_type: type) -> list:
    """
    Retrieves a list of functions associated with the given type.

    Args:
        object_type (type): Type of object to retrieve functions from.

    Returns: 
        list: List of functions that can be used to modify the given object type.
    """
    attribute_list = dir(object_type)
    method_list = [attr for attr in attribute_list if callable(getattr(object_type, attr)) and not attr.startswith("_")]
    return method_list

def _get_function_arguments(object_type: type, function_name: str) -> list:
    """
    Retrieves a list of arguments for a given function.
    
    Args:
        object_type (type): Type of object to retrieve arguments from.
        function_name (str): Name of the function to retrieve arguments from.
    
    Returns: 
        list: List of arguments for the given function.
    """
    return inspect.getfullargspec(getattr(object_type, function_name)).args

def _get_default_arguments(object_type: type, function_name: str) -> list:
    """
    Retrieves a list of default arguments for a given function.
    
    Args:
        object_type (type): Type of object to retrieve default arguments from.
        function_name (str): Name of the function to retrieve default arguments from.
    
    Returns: 
        list: List of default arguments for the given function.
    """
    default_arguments = getattr(object_type, function_name).__defaults__
    if(default_arguments is None):
        return []
    
    default_arguments = _recursive_parse_enum_to_string(default_arguments)
    print(default_arguments)
    return default_arguments

def _recursive_parse_enum_to_string(value) -> list:
    """
    Recursively parses a value.
    
    Args:
        value (object): Value to parse.
    """
    
    if type(value)==list or type(value)==tuple:
        return [_recursive_parse_enum_to_string(item) for item in value]
    elif isinstance(value, Enum):
        # print("CONVERTED"*100)
        return _convert_enum_instance_to_string(value)
    # print("Here")
    return value    

def _convert_enum_instance_to_string(enum_instance: object) -> str:
    """
    Converts an enum instance to a string.

    Args:
        enum_instance (Enum): Enum instance to convert to string.

    Returns:
        str: String representation of the enum instance.
    """
    try:
        instance_name = enum_instance.name
        enum_name = enum_instance.__class__.__name__
    except:
        None
        
    return f"{enum_name}.{instance_name}"

# May have to add key word arguments to this function
def get_all_functions_and_arguments(object_type: type) -> dict:
    """
    Retrieves a dictionary with the functions as keys and the arguments for each function as values.

    Args:
        object_type (type): Type of object to retrieve functions and arguments from.

    Returns: 
        dict: Dictionary with the map functions as keys and the arguments for each function as values.
    """
    functions = _get_functions(object_type)
    functions_and_arguments = {}
    
    for function_name in functions:
        # print(function_name)
        arguments = _get_function_arguments(object_type, function_name)
        defaults = _get_default_arguments(object_type, function_name)
        defaults = [None] * (len(arguments) - len(defaults)) + list(defaults)
        defaults = [str(default).replace("\'", '\"') for default in defaults]
        functions_and_arguments[function_name] = [list(arg_def) for arg_def in list(zip(arguments, defaults))]
        # functions_and_arguments[function_name] = json.dumps(functions_and_arguments[function_name])
        print(function_name)
        print(functions_and_arguments[function_name])
    
    return functions_and_arguments

def _convert_map_value_to_string(value: tuple) -> str:
    """
    Converts a map value to a string.
    
    Args:
        value (tuple): Value to convert to string.
    """
    if value == None:
        raise ValueError("Value cannot be None")
    elif len(value) != 2:
        raise ValueError("Value must be a tuple of length 2")
    elif type(value) == tuple and len(value) == 2:
        try:
            return str(value[0]), str(value[1])
        except:
            print(value[0], value[1])
            return "ERROR"

    raise ValueError("Unknown Parse Error")

def serialize_map_layer(map: Map, map_layer_type: MapLayerType):
    """
    Convert a map layer type into a dictionary.

    Args:
        map (Map): Map object to modify.
        map_layer_type (MapLayerType): Map layer type to serialize.
    
    Returns:
        dict: Serialized map layer.
    """
    map_layer = map.get_map_layer(map_layer_type)
    map_layer_array = map_layer.array

    serialized_map_layer = []
    for i in range(len(map_layer_array)):
        serialized_map_layer.append([])
        for j in range(len(map_layer_array[i])):
            
            try:
                [aoe2_object_string, player_id_string] = _convert_map_value_to_string(map_layer_array[i][j])
            except:
                print("HERE"*100)
                print(map_layer_array[i][j])
                raise ValueError("Error parsing map layer")
            serialized_map_layer[i].append([aoe2_object_string, player_id_string])
    
    return serialized_map_layer

def serialize_map(map: Map) -> json:
    """
    Convert a map into a dictionary.

    Args:
        map (Map): Map object to modify.
    
    Returns:
        dict: Serialized map in json format.
    
    Example:
        json['map_size'] = 100
        json['layers'] = dict()
        json['layers']['TERRAIN'] = dict()
        json['layers']['TERRAIN'][0][0] = dict()
        json['layers']['TERRAIN'][0][0]['object'] = 'GRASS'
        json['layers']['TERRAIN'][0][0]['playerid'] = 'GAIA'
    """
    serialized_map = dict()
    serialized_map['map_size'] = map.size
    serialized_map['layers'] = dict()

    for map_layer_type in MapLayerType:
        map.get_map_layer(map_layer_type)
        serialized_map['layers'][str(map_layer_type)] = serialize_map_layer(map, map_layer_type)
    
    return serialized_map

def deserialize_map(serialized_map: dict) -> Map:
    """
    Convert a dictionary into a map.

    Args:
        serialized_map (dict): Dictionary to convert to map.

    Returns:
        Map: Map object.
    """
    map_size = serialized_map['map_size']
    map = Map(map_size)

    for map_layer_type_string in serialized_map['layers']:
        
        serialized_map_layer = serialized_map['layers'][map_layer_type_string]
        map_layer_type = _convert_value_to_enum(map_layer_type_string)
        for i in range(len(serialized_map_layer)):
            for j in range(len(serialized_map_layer[i])):
                [aoe2_object_string, player_id_string] = serialized_map_layer[i][j]
                try:
                    aoe2_object = int(aoe2_object_string)
                except:
                    aoe2_object = _convert_value_to_enum(aoe2_object_string)
                player_id = _convert_value_to_enum(player_id_string)
                
                map.set_point(i, j, aoe2_object, map_layer_type, player_id)
    return map



def _string_to_player_id(player_id_string):
    """
    Convert a string to a player id.

    Args:
        player_id_string (str): String to convert to player id.
    """
    
    
    try:
        player_id = PlayerId[player_id_string]
    except KeyError:
        raise ValueError("Player id string is not valid")

def _string_to_array(array_string):
    """
    Convert a string to an array.

    Args:
        array_string (list): String to convert to array.
    """
    json.loads(array_string)

import ast

def _get_enum_list(enum_type: type) -> list:
    """
    Get a list of units.
    """
    enum_element_list = []
    enum_name = enum_type.__name__
    
    for element in enum_type:
        enum_element_list.append(f"{enum_name}.{element.name}")
    
    return sorted(enum_element_list)