"""
TODO: Add module docstring.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.maplayer import MapLayer
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.common.constants.constants import DisplacementType


class Map:
    """
    Class for the Age of Empires Map layers
    """

    def __init__(self, size: int = 100):
        """
        Initializes map object for internal map representation.

        Args:
            size: Size of the map.
        """
        # TEMPLATE NAMES, MULTIPLE INHERITANCE, init, AAHGHG
        self.template_names: dict = {}
        self.size = size

        self.unit_map_layer = MapLayer(MapLayerType.UNIT, self.size)
        self.zone_map_layer = MapLayer(MapLayerType.ZONE, self.size)
        self.terrain_map_layer = MapLayer(MapLayerType.TERRAIN, self.size)
        self.decor_map_layer = MapLayer(MapLayerType.DECOR, self.size)
        self.elevation_map_layer = MapLayer(MapLayerType.ELEVATION, self.size)

    def get_map_layer(self, map_layer_type: MapLayerType):
        """
        Gets the corresponding map layer from a map layer type.
        """

        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError("Map layer type is not a MapLayerType.")

        if map_layer_type == MapLayerType.ZONE:
            return self.zone_map_layer
        elif map_layer_type == MapLayerType.TERRAIN:
            return self.terrain_map_layer
        elif map_layer_type == MapLayerType.UNIT:
            return self.unit_map_layer
        elif map_layer_type == MapLayerType.DECOR:
            return self.decor_map_layer
        elif map_layer_type == MapLayerType.ELEVATION:
            return self.elevation_map_layer

        raise ValueError("Retrieving map layer from map layer type failed.")

    def get_all_map_layers(self) -> list[MapLayer]:
        """
        Gets all map layers.
        """
        return [
            self.unit_map_layer,
            self.zone_map_layer,
            self.terrain_map_layer,
            self.decor_map_layer,
            self.elevation_map_layer,
        ]

    def set_point(
        self,
        x: int,
        y: int,
        new_value: AOE2ObjectType | DisplacementType,
        map_layer_type: MapLayerType,
        player_id: PlayerId = PlayerId.GAIA,
    ):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        layer = self.get_map_layer(map_layer_type)
        layer.set_point(x, y, new_value, player_id)

    def get_dictionary_from_map_layer_type(self, map_layer_type: MapLayerType):
        """
        Gets the dictionary from a map layer type.
        """
        return self.get_map_layer(map_layer_type).get_dict()

    def get_array_from_map_layer_type(self, map_layer_type: MapLayerType):
        """
        Gets the array from a map layer type.
        """
        return self.get_map_layer(map_layer_type).get_array()

    def get_set_with_map_object(
        self,
        map_layer_type: MapLayerType,
        obj: MapObject,
    ):
        """
        Returns the array representation of the map layer with the object.
        """
        return self.get_map_layer(map_layer_type).get_set_with_map_object(obj)
