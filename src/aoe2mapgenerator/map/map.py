"""Map — top-level container for all AoE2 map layer data.

A ``Map`` is a Pydantic ``BaseModel`` composed of five ``MapLayer`` instances,
one per ``MapLayerType`` (UNIT, ZONE, TERRAIN, DECOR, ELEVATION).  It is the
primary data container passed between ``MapManager``, placers, and the
scenario serialiser.

Serialization
-------------
* ``model_dump()`` / ``model_validate()`` — Pydantic-style round-trip using the
  internal format expected by ``map_serialization.py``.
* ``serialize()`` / ``deserialize()`` — legacy JSON round-trip kept for backward
  compatibility with older scenario files.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.maplayer import MapLayer, MapLayerDictionary
from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.common.constants.constants import DisplacementType
from aoe2mapgenerator.serializer.base_serializer import Serializable
import ujson as json

# Dispatch table: MapLayerType → attribute name on the Map instance.
# Update this dict whenever a new MapLayerType is introduced.
_LAYER_ATTR: dict[MapLayerType, str] = {
    MapLayerType.UNIT: "unit_map_layer",
    MapLayerType.ZONE: "zone_map_layer",
    MapLayerType.TERRAIN: "terrain_map_layer",
    MapLayerType.DECOR: "decor_map_layer",
    MapLayerType.ELEVATION: "elevation_map_layer",
}


class Map(BaseModel):
    """
    Class for the Age of Empires Map layers

    BaseModel provides validation, serialization, and other features.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    size: int = 100
    template_names: dict[str, str] = Field(default_factory=dict)
    unit_map_layer: Optional[MapLayer] = Field(default=None, exclude=True)
    zone_map_layer: Optional[MapLayer] = Field(default=None, exclude=True)
    terrain_map_layer: Optional[MapLayer] = Field(default=None, exclude=True)
    decor_map_layer: Optional[MapLayer] = Field(default=None, exclude=True)
    elevation_map_layer: Optional[MapLayer] = Field(default=None, exclude=True)

    def __init__(self, size: int = 100, **data: Any):
        super().__init__(size=size, **data)

    def model_post_init(self, __context: Any) -> None:
        """Initialize map layers after model creation."""
        if self.unit_map_layer is None:
            self.unit_map_layer = MapLayer(map_layer_type=MapLayerType.UNIT, size=self.size)
        if self.zone_map_layer is None:
            self.zone_map_layer = MapLayer(map_layer_type=MapLayerType.ZONE, size=self.size)
        if self.terrain_map_layer is None:
            self.terrain_map_layer = MapLayer(map_layer_type=MapLayerType.TERRAIN, size=self.size)
        if self.decor_map_layer is None:
            self.decor_map_layer = MapLayer(map_layer_type=MapLayerType.DECOR, size=self.size)
        if self.elevation_map_layer is None:
            self.elevation_map_layer = MapLayer(map_layer_type=MapLayerType.ELEVATION, size=self.size)

    def get_map_layer(self, map_layer_type: MapLayerType) -> "MapLayer":
        """Return the MapLayer for the given layer type.

        Raises:
            ValueError: If ``map_layer_type`` is not a known layer.
        """
        attr = _LAYER_ATTR.get(map_layer_type)
        if attr is None:
            raise ValueError(
                f"Unknown MapLayerType {map_layer_type!r}. "
                f"Valid values: {list(_LAYER_ATTR)}"
            )
        return getattr(self, attr)

    def get_all_map_layers(self) -> list[MapLayer]:
        """
        Gets all map layers.
        """
        assert all([
            self.unit_map_layer is not None,
            self.zone_map_layer is not None,
            self.terrain_map_layer is not None,
            self.decor_map_layer is not None,
            self.elevation_map_layer is not None,
        ])
        return [
            self.unit_map_layer,
            self.zone_map_layer,
            self.terrain_map_layer,
            self.decor_map_layer,
            self.elevation_map_layer,
        ]

    def set_point(
        self,
        point: tuple[int, int],
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
        layer.set_point(point, new_value, player_id)

    def get_dictionary_from_map_layer_type(
        self, map_layer_type: MapLayerType
    ) -> MapLayerDictionary:
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

    def to_dict(self) -> dict[str, object]:
        assert all([
            self.unit_map_layer is not None,
            self.zone_map_layer is not None,
            self.terrain_map_layer is not None,
            self.decor_map_layer is not None,
            self.elevation_map_layer is not None,
        ])
        return {
            "_type": self.__class__.__name__,
            "unit_map_layer": self.unit_map_layer.to_dict(),
            "zone_map_layer": self.zone_map_layer.to_dict(),
            "terrain_map_layer": self.terrain_map_layer.to_dict(),
            "decor_map_layer": self.decor_map_layer.to_dict(),
            "elevation_map_layer": self.elevation_map_layer.to_dict(),
        }

    def serialize(self) -> str:
        """
        Serializes the Map object to a JSON string (legacy method).
        """
        return json.dumps(self.to_dict())
    
    def model_dump_json(self) -> str:
        """
        Pydantic-style JSON serialization.
        """
        return json.dumps(self.model_dump())
    
    def model_dump(self) -> dict[str, Any]:
        """
        Pydantic-style dict serialization.
        """
        assert all([
            self.unit_map_layer is not None,
            self.zone_map_layer is not None,
            self.terrain_map_layer is not None,
            self.decor_map_layer is not None,
            self.elevation_map_layer is not None,
        ])
        return {
            "size": self.size,
            "template_names": self.template_names,
            "unit_map_layer": self.unit_map_layer.model_dump(),
            "zone_map_layer": self.zone_map_layer.model_dump(),
            "terrain_map_layer": self.terrain_map_layer.model_dump(),
            "decor_map_layer": self.decor_map_layer.model_dump(),
            "elevation_map_layer": self.elevation_map_layer.model_dump(),
        }
    
    @staticmethod
    def model_validate_json(json_string: str) -> "Map":
        """
        Pydantic-style JSON deserialization.
        """
        json_dict = json.loads(json_string)
        return Map.model_validate(json_dict)
    
    @classmethod
    def model_validate(cls, json_dict: dict[str, Any]) -> "Map":
        """
        Pydantic-style dict deserialization.
        """
        new_map = cls(size=json_dict["size"])
        new_map.template_names = json_dict.get("template_names", {})
        
        # Deserialize map layers
        for layer_name in ["unit_map_layer", "zone_map_layer", "terrain_map_layer", "decor_map_layer", "elevation_map_layer"]:
            layer_data = json_dict[layer_name]
            map_layer_type = Serializable.deserialize_prim(layer_data["map_layer_type"])
            size = layer_data["size"]
            layer = MapLayer(map_layer_type=map_layer_type, size=size)
            
            # Restore array data
            for i, row in enumerate(layer_data["array"]):
                for j, cell_data in enumerate(row):
                    obj_type = Serializable.deserialize_prim(cell_data["obj_type"])
                    player_id = Serializable.deserialize_prim(cell_data["player_id"])
                    layer.set_point((i, j), obj_type, player_id)
            
            setattr(new_map, layer_name, layer)
        
        return new_map

    @staticmethod
    def deserialize(json_string: str | dict[str, object]) -> "Map":
        json_dict: dict[str, object]
        if isinstance(json_string, dict):
            json_dict = json_string
        else:
            json_dict = json.loads(json_string)

        new_map = Map()

        # Restore size if serialised (added in map_serialization v2).
        if "size" in json_dict:
            new_map.size = int(json_dict["size"])  # type: ignore[assignment]

        # Cast to the expected type for MapLayer.deserialize
        unit_data = json_dict["unit_map_layer"]
        zone_data = json_dict["zone_map_layer"]
        terrain_data = json_dict["terrain_map_layer"]
        decor_data = json_dict["decor_map_layer"]
        elevation_data = json_dict["elevation_map_layer"]

        assert isinstance(unit_data, (str, dict))
        assert isinstance(zone_data, (str, dict))
        assert isinstance(terrain_data, (str, dict))
        assert isinstance(decor_data, (str, dict))
        assert isinstance(elevation_data, (str, dict))

        new_map.unit_map_layer = MapLayer.deserialize(unit_data)  # type: ignore
        new_map.zone_map_layer = MapLayer.deserialize(zone_data)  # type: ignore
        new_map.terrain_map_layer = MapLayer.deserialize(terrain_data)  # type: ignore
        new_map.decor_map_layer = MapLayer.deserialize(decor_data)  # type: ignore
        new_map.elevation_map_layer = MapLayer.deserialize(elevation_data)  # type: ignore

        return new_map

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Map):
            return NotImplemented
        return self.serialize() == other.serialize()
