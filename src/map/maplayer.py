"""
TODO: Add module documentation.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from typing import Any, List

from aoe2mapgenerator.src.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    DEFAULT_PLAYER,
)
from aoe2mapgenerator.src.common.constants.default_objects import DEFAULT_EMPTY_OBJECT
from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.common.types import AOE2ObjectType
from aoe2mapgenerator.src.map.map_object import MapObject
from aoe2mapgenerator.src.serializer.base_serializer import Serializable
import ujson as json

MapLayerArray = List[List[MapObject]]
"""
MapLayerArray: 2D array representation of the map layer. Each element is a MapObject.
"""
MapLayerDictionary = dict[MapObject, set[tuple[int, int]]]
"""
MapLayerDictionary: Dictionary representation of the map layer. Each key is a MapObject and each value is a set of points.
"""


class MapLayer(Serializable):
    """
    Single Map type constructor.
    """

    def __init__(self, map_layer_type: MapLayerType, size: int = 100) -> None:

        self.map_layer_type = map_layer_type
        self.size = size
        # Create a 2D array of the given size.
        # These objects will all reference the same default object.
        # This is done to save memory.
        self.array = [[DEFAULT_EMPTY_OBJECT for i in range(size)] for j in range(size)]
        self.dict = _create_dict(self.array)

    def set_point(
        self,
        point: tuple[int, int],
        new_value: AOE2ObjectType,
        player_id: PlayerId = PlayerId.GAIA,
    ) -> None:
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            point: Tuple of x and y coordinates.
            new_value: New value to set.
            player_id: Player ID to set.
        """
        x, y = point

        new_obj = MapObject(new_value, player_id)
        old_obj = self.array[x][y]

        # Retrieve correct dictionary and array.
        dictionary = self.dict
        array = self.array

        # Remove element from the dictionary.
        dictionary[old_obj].remove((x, y))

        # Remove entire dictionary entry if there are not elements left.
        if len(dictionary[old_obj]) == 0:
            dictionary.pop(old_obj, None)

        # Assign new value to the array.
        array[x][y] = new_obj

        # Add the value to the dictionary.
        if new_obj in dictionary:
            dictionary[new_obj].add((x, y))
        else:
            dictionary[new_obj] = {(x, y)}

    def get_array_of_points(self, map_object: MapObject) -> set[tuple[int, int]]:
        """
        Gets the set of points that have the object.
        """
        return self.dict[map_object]

    def get_array(self) -> MapLayerArray:
        """
        Returns the array representation of the map layer.
        """
        return self.array

    def get_dict(self) -> MapLayerDictionary:
        """
        Returns the dictionary representation of the map layer.
        """
        return self.dict

    def get_set_with_map_object(self, obj: MapObject):
        """
        Returns the array representation of the map layer with the object.
        """
        if obj not in self.dict:
            return set()
        return self.dict[obj]

    def to_dict(self):
        return {
            "_type": self.__class__.__name__,
            "layer": self.serialize_prim(self.map_layer_type),
            "size": self.serialize_prim(self.size),
            "array": [[cell.to_dict() for cell in row] for row in self.array],
        }

    def serialize(self) -> Any:
        return self.dump(self.to_dict())

    @staticmethod
    def deserialize(json_string: str | dict) -> "MapLayer":

        json_data: dict

        if isinstance(json_string, dict):
            json_data = json_string
        else:
            json_data = json.loads(json_string)

        new_layer = MapLayer(
            MapLayer.deserialize_prim(json_data["layer"]),
            int(json_data["size"]),
        )

        for i, row in enumerate(json_data["array"]):
            for j, cell in enumerate(json_data["array"][i]):
                map_object = MapObject.deserialize(cell)

                new_layer.set_point(
                    (i, j), map_object.get_obj_type(), map_object.get_player_id()
                )

        return new_layer


def _create_dict(array: list[list[MapObject]]) -> MapLayerDictionary:
    """
    Creates a set representation from the array.
    """

    new_dict: MapLayerDictionary = {}

    for i, row in enumerate(array):
        for j, cell in enumerate(row):
            if cell in new_dict:
                new_dict[cell].add((i, j))
            else:
                new_dict[cell] = {(i, j)}

    return new_dict
