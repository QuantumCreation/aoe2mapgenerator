from common.enums.enum import ValueType
from typing import Union
from AoE2ScenarioParser.datasets.players import PlayerId

class MapUtilsMixin():
    """
    TODO
    """

    def get_dictionary_from_value_type(self, value_type):
        """
        Gets the corresponding dictionary from a value type.

        Args:
            value_type: Type of the value or object.
        """
        if not isinstance(value_type, ValueType):
            raise ValueError("Value type is not valid.")

        if value_type == ValueType.ZONE:
            return self.zone_dict
        elif value_type == ValueType.TERRAIN:
            return self.terrain_dict
        elif value_type == ValueType.UNIT:
            return self.object_dict
        elif value_type == ValueType.DECOR:
            return self.decor_dict
        elif value_type == ValueType.ELEVATION:
            return self.elevation_dict
        
        raise ValueError("Retrieving dictionary from value type failed.")
    
    def get_array_from_value_type(self, value_type):
        """
        Gets the corresponding array form a value type.

        Args:
            value_type: Type of the value or object.
        """
        if value_type == ValueType.ZONE:
            return self.zone_array
        elif value_type == ValueType.TERRAIN:
            return self.terrain_array
        elif value_type == ValueType.UNIT:
            return self.object_array
        elif value_type == ValueType.DECOR:
            return self.decor_array
        elif value_type == ValueType.ELEVATION:
            return self.elevation_array
        
        raise ValueError("Retrieving array from value type failed.")

    def set_point(self, x, y, new_value, value_type: Union[ValueType, int], player_id : PlayerId = PlayerId.GAIA):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        # Retrieve correct dictionary and array.
        d = self.get_dictionary_from_value_type(value_type)
        a = self.get_array_from_value_type(value_type)
        
        # Remove element from the dictionary.
        d[a[x][y]].remove((x,y))

        # Remove entire dictionary entry if there are not elements left.
        if len(d[a[x][y]]) == 0:
            d.pop(a[x][y], None)

        # Assign new value to the array.
        a[x][y] = (new_value, player_id)

        # Add the value to the dictionary.
        if (new_value, player_id) in d:
            d[a[x][y]].add((x,y))
        else:
            d[a[x][y]] = {(x,y)}