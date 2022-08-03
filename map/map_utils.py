from common.enums.enum import ValueType

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