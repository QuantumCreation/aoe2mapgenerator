from aoe2mapgenerator.map.map import Map
import inspect
import json
from aoe2mapgenerator.common.enums.enum import MapLayerType


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
        print(function_name)
        functions_and_arguments[function_name] = _get_function_arguments(object_type, function_name)
        print(functions_and_arguments[function_name])
    
    return functions_and_arguments

def fun():
    pass

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
        return str(value[0]), value[1]._name_ 

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
            
            [aoe2_object_string, player_id_string] = _convert_map_value_to_string(map_layer_array[i][j])

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
