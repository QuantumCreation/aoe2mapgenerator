"""MapLayer — a single typed 2-D grid of MapObjects.

Each ``MapLayer`` maintains two complementary representations of the same data:

* ``_id_array``   — ``np.ndarray`` of shape ``(size, size)`` and dtype
  ``uint16`` that stores per-cell indices into ``_registry``.  This gives
  O(1) spatial look-ups with ~40× less memory than a
  ``list[list[MapObject]]`` (≈80 KB vs ≈3 MB for a 200×200 grid).
* ``dictionary``  — ``dict[MapObject, set[tuple[int,int]]]`` for O(1) reverse
  look-ups of *all* coordinates occupied by a given object.
* ``_registry``   — ordered ``list[MapObject]`` of distinct objects seen so
  far in this layer.  ``_registry_map`` is its O(1) inverse index.
  Index 0 is always ``DEFAULT_EMPTY_OBJECT`` so that the zero-initialised
  ``_id_array`` is correct from construction.

All three representations are kept in sync by ``set_point()``.  Do **not**
mutate ``_id_array``, ``_registry``, ``_registry_map``, or ``dictionary``
directly.

``get_array()`` reconstructs the legacy ``list[list[MapObject]]`` on demand
(O(size²)); use it only where full Python-level iteration is required (e.g.
the scenario writer).  Prefer ``get_object_at_point()`` for point access.
"""

from __future__ import annotations

import numpy as np

from AoE2ScenarioParser.datasets.players import PlayerId

from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr

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
"""2-D list of MapObjects (legacy representation, reconstructed on demand)."""

MapLayerDictionary = dict[MapObject, set[tuple[int, int]]]
"""Reverse index: MapObject → set of (x, y) coordinates it occupies."""

_MAX_REGISTRY_SIZE: int = 65_535
"""
Maximum number of distinct MapObject types per layer (uint16 limit).
Real maps typically use fewer than 100 unique entries.
"""


class MapLayer(BaseModel):
    """Single Map-layer constructor.

    Stores tile data internally in a compact ``uint16`` NumPy ID array backed
    by a small object registry.  The public API is fully backward-compatible.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    map_layer_type: Optional[MapLayerType]
    size: Optional[int] = 100

    # ------------------------------------------------------------------
    # Private storage — do NOT access these fields from outside MapLayer
    # ------------------------------------------------------------------

    # Ordered list of distinct MapObjects; index 0 == DEFAULT_EMPTY_OBJECT.
    _registry: list[MapObject] = PrivateAttr(default_factory=list)
    # Inverse of _registry: MapObject → uint16 index into _registry.
    _registry_map: dict[MapObject, int] = PrivateAttr(default_factory=dict)
    # shape (size, size), dtype uint16 — each cell stores an index into _registry.
    _id_array: Optional[np.ndarray] = PrivateAttr(default=None)

    # Reverse spatial index  (excluded from Pydantic serialisation)
    dictionary: Optional[MapLayerDictionary] = Field(default=None, exclude=True)

    # ------------------------------------------------------------------
    def model_post_init(self, __context: Any) -> None:  # noqa: ANN001
        """Initialise the registry, ID array, and reverse dictionary."""
        size: int = self.size or 100

        # Registry: index 0 is always the empty object so np.zeros() is valid.
        self._registry = [DEFAULT_EMPTY_OBJECT]
        self._registry_map = {DEFAULT_EMPTY_OBJECT: 0}

        # All cells start as DEFAULT_EMPTY_OBJECT (registry index 0).
        self._id_array = np.zeros((size, size), dtype=np.uint16)

        # All (size²) points belong to DEFAULT_EMPTY_OBJECT initially.
        all_points: set[tuple[int, int]] = {
            (i, j) for i in range(size) for j in range(size)
        }
        self.dictionary = {DEFAULT_EMPTY_OBJECT: all_points}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_register(self, obj: MapObject) -> int:
        """Return the uint16 registry index for *obj*, registering it if new.

        Raises:
            OverflowError: if registry would exceed ``_MAX_REGISTRY_SIZE``.
        """
        idx = self._registry_map.get(obj)
        if idx is None:
            idx = len(self._registry)
            if idx >= _MAX_REGISTRY_SIZE:
                raise OverflowError(
                    f"MapLayer registry full: {_MAX_REGISTRY_SIZE} unique object "
                    "types already registered in this layer."
                )
            self._registry.append(obj)
            self._registry_map[obj] = idx
        return idx

    # ------------------------------------------------------------------
    # Public mutation API
    # ------------------------------------------------------------------

    def set_point(
        self,
        point: tuple[int, int],
        new_value: AOE2ObjectType,
        player_id: PlayerId = PlayerId.GAIA,
    ) -> None:
        """Update a single cell in all three internal representations.

        Args:
            point:     ``(x, y)`` coordinates.
            new_value: New object type to place.
            player_id: Owning player.
        """
        assert self._id_array is not None and self.dictionary is not None

        x, y = point
        new_obj = MapObject(new_value, player_id)

        # Retrieve the current object from the compact array.
        old_id: int = int(self._id_array[x, y])
        old_obj: MapObject = self._registry[old_id]

        # --- Remove old object from reverse dictionary ----------------
        old_pts = self.dictionary[old_obj]
        old_pts.discard((x, y))
        if not old_pts:
            del self.dictionary[old_obj]

        # --- Update compact ID array ----------------------------------
        new_id: int = self._get_or_register(new_obj)
        self._id_array[x, y] = new_id

        # --- Add new object to reverse dictionary ---------------------
        if new_obj in self.dictionary:
            self.dictionary[new_obj].add((x, y))
        else:
            self.dictionary[new_obj] = {(x, y)}

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------

    def get_array_of_points(self, map_object: MapObject) -> set[tuple[int, int]]:
        """Returns the set of all points that currently hold *map_object*."""
        assert self.dictionary is not None
        return self.dictionary[map_object]

    def get_array(self) -> MapLayerArray:
        """Reconstruct and return the full ``list[list[MapObject]]``.

        This is an O(size²) operation; call only when full iteration is needed.
        """
        assert self._id_array is not None
        registry = self._registry
        rows, cols = self._id_array.shape
        return [
            [registry[int(self._id_array[i, j])] for j in range(cols)]
            for i in range(rows)
        ]

    def get_dict(self) -> MapLayerDictionary:
        """Returns the reverse-index dictionary."""
        assert self.dictionary is not None
        return self.dictionary

    def get_set_with_map_object(self, obj: MapObject) -> set[tuple[int, int]]:
        """Returns all points occupied by *obj*, or an empty set if absent."""
        assert self.dictionary is not None
        return self.dictionary.get(obj, set())

    def get_object_at_point(self, point: tuple[int, int]) -> MapObject:
        """Returns the MapObject stored at *(x, y)*."""
        assert self._id_array is not None
        return self._registry[int(self._id_array[point[0], point[1]])]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        assert self._id_array is not None
        registry = self._registry
        return {
            "_type": self.__class__.__name__,
            "layer": Serializable.serialize_prim(self.map_layer_type),
            "size": Serializable.serialize_prim(self.size),
            "array": [
                [registry[int(id_)].to_dict() for id_ in row]
                for row in self._id_array
            ],
        }

    def serialize(self) -> str:
        """Legacy serialization for backwards compatibility."""
        return json.dumps(self.to_dict())

    def model_dump_json(self) -> str:
        """Pydantic-style JSON serialization."""
        return json.dumps(self.model_dump())

    def model_dump(self) -> dict[str, Any]:
        """Pydantic-style dict serialization."""
        assert self._id_array is not None
        registry = self._registry
        return {
            "map_layer_type": Serializable.serialize_prim(self.map_layer_type),
            "size": self.size,
            "array": [
                [registry[int(id_)].model_dump() for id_ in row]
                for row in self._id_array
            ],
        }

    @staticmethod
    def deserialize(json_string: str | dict[str, Any]) -> "MapLayer":
        """Reconstruct a MapLayer from its serialized form."""
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
            for j, cell in enumerate(row):
                map_object = MapObject.deserialize(cell)
                new_layer.set_point(
                    (i, j), map_object.get_obj_type(), map_object.get_player_id()
                )

        return new_layer
