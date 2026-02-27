"""MapLayer — a single typed 2-D grid of MapObjects.

Each ``MapLayer`` maintains two complementary representations of the same data:

* ``array``      — ``list[list[MapObject]]`` for O(1) spatial look-ups by (x, y).
* ``dictionary`` — ``dict[MapObject, set[tuple[int,int]]]`` for O(1) reverse
  look-ups of *all* coordinates occupied by a given object.

Both representations are kept in sync by ``set_point()``.  Do not mutate
``array`` or ``dictionary`` directly.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    DEFAULT_PLAYER,
)
from aoe2mapgenerator.common.constants.default_objects import DEFAULT_EMPTY_OBJECT
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.serializer.base_serializer import Serializable
try:
    import ujson as json
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    import json

MapLayerArray = List[List[MapObject]]
"""
MapLayerArray: 2D array representation of the map layer. Each element is a MapObject.
"""
MapLayerDictionary = dict[MapObject, set[tuple[int, int]]]
"""
MapLayerDictionary: Dictionary representation of the map layer. Each key is a MapObject and each value is a set of points.
"""


class MapLayer(BaseModel):
    """
    Single Map type constructor.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    map_layer_type: Optional[MapLayerType]
    size: Optional[int] = 100
    array: Optional[MapLayerArray] = Field(default=None, exclude=True)
    dictionary: Optional[MapLayerDictionary] = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        """Initialize the array and dictionary after model creation."""
        if self.array is None:
            array_data = [[DEFAULT_EMPTY_OBJECT for i in range(self.size)] for j in range(self.size)]
            self.array = array_data
            self.dictionary = _create_dict(array_data)

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
        assert self.array is not None and self.dictionary is not None
        x, y = point

        new_obj = MapObject(new_value, player_id)
        old_obj = self.array[x][y]

        # Retrieve correct dictionary and array.
        dictionary = self.dictionary
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
        assert self.dictionary is not None
        return self.dictionary[map_object]

    def get_array(self) -> MapLayerArray:
        """
        Returns the array representation of the map layer.
        """
        assert self.array is not None
        return self.array

    def get_dict(self) -> MapLayerDictionary:
        """
        Returns the dictionary representation of the map layer.
        """
        assert self.dictionary is not None
        return self.dictionary

    def get_set_with_map_object(self, obj: MapObject) -> set[tuple[int, int]]:
        """
        Returns the array representation of the map layer with the object.
        """
        assert self.dictionary is not None
        if obj not in self.dictionary:
            return set()
        return self.dictionary[obj]

    def get_object_at_point(self, point: tuple[int, int]) -> MapObject:
        """
        Returns the object at the given point.
        """
        assert self.array is not None
        return self.array[point[0]][point[1]]

    def to_dict(self) -> dict[str, Any]:
        assert self.array is not None
        return {
            "_type": self.__class__.__name__,
            "layer": Serializable.serialize_prim(self.map_layer_type),
            "size": Serializable.serialize_prim(self.size),
            "array": [[cell.to_dict() for cell in row] for row in self.array],
        }

    def serialize(self) -> str:
        """Legacy serialization for backwards compatibility."""
        data: dict[str, Any] = self.to_dict()
        return json.dumps(data)
    
    def model_dump_json(self) -> str:
        """Pydantic-style JSON serialization."""
        return json.dumps(self.model_dump())
    
    def model_dump(self) -> dict[str, Any]:
        """Pydantic-style dict serialization."""
        assert self.array is not None
        return {
            "map_layer_type": Serializable.serialize_prim(self.map_layer_type),
            "size": self.size,
            "array": [[cell.model_dump() for cell in row] for row in self.array],
        }

    @staticmethod
    def deserialize(json_string: str | dict[str, Any]) -> "MapLayer":

        json_data: dict[str, Any]

        if isinstance(json_string, dict):
            json_data = json_string
        else:
            json_data = json.loads(json_string)

        new_layer = MapLayer(
            map_layer_type=Serializable.deserialize_prim(json_data["layer"]),
            size=int(json_data["size"]),
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
