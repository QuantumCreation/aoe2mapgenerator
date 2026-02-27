"""Internal dataclasses for the CITY template deterministic layout pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection

Point = tuple[int, int]


@dataclass(frozen=True)
class GateAnchorSpec:
    """Intended gate anchor on the wall for a sector."""

    sector: str
    target_wall_anchor: Point
    priority: int
    expected_orientation: str
    inward_vector: Point
    outward_vector: Point


@dataclass(frozen=True)
class PlacedGate:
    """Actual gate metadata captured after gate placement."""

    sector: str
    gate_center_tile: Point
    gate_object_name: str
    footprint_tiles: list[Point]
    inner_approach_tile: Point
    outer_approach_tile: Point


@dataclass(frozen=True)
class CitySlotSpec:
    """Deterministic ward slot for prefab placement."""

    slot_id: str
    ward: str
    anchor: Point
    orientation: str
    allowed_prefabs: tuple[str, ...]
    required: bool
    variant_key: str


@dataclass(frozen=True)
class PrefabPlacement:
    """One exact tile placement in a prefab."""

    offset: Point
    layer: MapLayerType
    obj_type: Any
    player_id: PlayerId
    margin: int = 0


@dataclass(frozen=True)
class PrefabSpec:
    """A multi-layer deterministic prefab stamp."""

    name: str
    footprint_mask: list[Point]
    reserved_mask: list[Point]
    unit_tiles: list[PrefabPlacement]
    terrain_tiles: list[PrefabPlacement]
    decor_tiles: list[PrefabPlacement]
    allowed_transforms: tuple[str, ...] = ("identity",)


@dataclass
class CityLayoutPlan:
    """Computed macro layout for the CITY template."""

    center: Point
    radius_wall: int
    radius_patrol_ring: int
    radius_main_ring: int
    radius_inner_ring: int
    core_mask: PointCollection
    interior_mask: PointCollection
    ward_masks: dict[str, PointCollection]
    road_masks: dict[str, PointCollection] = field(default_factory=dict)
    plaza_masks: dict[str, PointCollection] = field(default_factory=dict)
    gate_specs: list[GateAnchorSpec] = field(default_factory=list)
    slot_specs: list[CitySlotSpec] = field(default_factory=list)
    aggregate_trigger_areas: dict[str, tuple[int, int, int, int]] = field(default_factory=dict)

