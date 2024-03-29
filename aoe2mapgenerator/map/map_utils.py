from aoe2mapgenerator.common.enums.enum import MapLayerType
from typing import Union
from AoE2ScenarioParser.datasets.players import PlayerId
import functools

class MapUtilsMixin():
    """
    TODO
    """

    def get_dictionary_from_map_layer_type(self, map_layer_type: Union[MapLayerType, int]) -> dict:
        """
        Gets the corresponding dictionary from a value type.

        Args:
            map_layer_type: Type of the value or object.
        
        Returns: 
            Dictionary mapping the value to the set of points that have that value.
        """
        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError(f"The value {map_layer_type} has a type of {type(map_layer_type)} which is not a valid MapLayerType.")

        return self.get_map_layer(map_layer_type).dict
    
    def get_array_from_map_layer_type(self, map_layer_type: Union[MapLayerType, int]) -> list:
        """
        Gets the corresponding array from a value type.

        Args:
            map_layer_type: Type of the value or object.
        
        Returns:
            Array representation of the map layer.
        """
        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError("Value type is not valid.")
        
        return self.get_map_layer(map_layer_type).array

    def get_intersection_of_spaces(self, map_layer_type_list: list, array_space_type_list: list) -> list:
        """
        Gets the union of the different spaces.

        Args:
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns: 
            list: List of points that are in the intersection of the spaces.
        """

        # This is the old code, which is not correct.
        # sets = []

        # for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
        #     sets.append(self.get_dictionary_from_map_layer_type(map_layer_type)[array_space_type])

        sets = []

        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):

            dictionary = self.get_dictionary_from_map_layer_type(map_layer_type)

            # If the space type is None, then it is ignored for the purpose of the union.
            # This means that if we only have None as the array_Space_type, then the union will be empty.
            # However, if one of the other array_space_types is not None, then the union will be the union of all the non-None types.
            if array_space_type is None:
                continue
            
            if type(array_space_type) == list:
                array_space_type = tuple(array_space_type)
            
            if array_space_type not in dictionary:
                raise ValueError(f"Array space type {array_space_type} is not valid for map layer {map_layer_type}.")
            
            s = dictionary[array_space_type]
            
            sets.append(s)

        return functools.reduce(lambda a, b: a & b, sets)

