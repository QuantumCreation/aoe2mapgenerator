from common.enums.enum import MapLayerType
from typing import Union
from AoE2ScenarioParser.datasets.players import PlayerId

class MapUtilsMixin():
    """
    TODO
    """

    def get_dictionary_from_map_layer_type(self, map_layer_type: Union[MapLayerType, int]):
        """
        Gets the corresponding dictionary from a value type.

        Args:
            map_layer_type: Type of the value or object.
        """
        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError("Value type is not valid.")

        return self.get_map_layer(map_layer_type).dict
    
    def get_array_from_map_layer_type(self, map_layer_type: Union[MapLayerType, int]):
        """
        Gets the corresponding array from a value type.

        Args:
            map_layer_type: Type of the value or object.
        """
        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError("Value type is not valid.")
        
        return self.get_map_layer(map_layer_type).array
        
        raise ValueError("Retrieving array from value type failed.")

