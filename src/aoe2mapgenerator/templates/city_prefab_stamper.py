"""Exact multi-layer prefab stamping for the CITY template."""

from __future__ import annotations

from dataclasses import dataclass

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import CheckPlacementReturnTypes, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.city_layout_plan import PrefabPlacement, PrefabSpec
from aoe2mapgenerator.units.placers.placer_configs import PlaceIfPossibleConfig
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection

Point = tuple[int, int]


def _transform_offset(offset: Point, transform: str) -> Point:
    dr, dc = offset
    if transform == "identity":
        return (dr, dc)
    if transform == "rot90":
        return (dc, -dr)
    if transform == "rot180":
        return (-dr, -dc)
    if transform == "rot270":
        return (-dc, dr)
    if transform == "mirror":
        return (dr, -dc)
    raise ValueError(f"Unsupported prefab transform '{transform}'")


def _apply_transform(anchor: Point, offset: Point, transform: str) -> Point:
    ddr, ddc = _transform_offset(offset, transform)
    return (anchor[0] + ddr, anchor[1] + ddc)


@dataclass
class StampResult:
    """Result of a prefab stamp attempt."""

    success: bool
    reserved_points: set[Point]
    unit_points: set[Point]
    terrain_points: set[Point]
    decor_points: set[Point]


class CityPrefabStamper:
    """Stamp exact multi-layer prefabs onto the map."""

    def __init__(
        self,
        map_manager: IMapManager,
        unit_point_collection: PointCollection,
        surface_allowed_points: set[Point],
    ) -> None:
        self.map_manager = map_manager
        self.unit_point_collection = unit_point_collection
        self.surface_allowed_points = surface_allowed_points

    def _placement_points(self, placements: list[PrefabPlacement], anchor: Point, transform: str) -> list[tuple[PrefabPlacement, Point]]:
        return [(placement, _apply_transform(anchor, placement.offset, transform)) for placement in placements]

    def _mask_points(self, offsets: list[Point], anchor: Point, transform: str) -> set[Point]:
        return {_apply_transform(anchor, offset, transform) for offset in offsets}

    def can_stamp(
        self,
        spec: PrefabSpec,
        anchor: Point,
        transform: str = "identity",
        reserved_points: set[Point] | None = None,
    ) -> bool:
        if transform not in spec.allowed_transforms:
            return False
        reserved_points = reserved_points or set()
        footprint = self._mask_points(spec.footprint_mask + spec.reserved_mask, anchor, transform)
        if any(point not in self.surface_allowed_points for point in footprint):
            return False
        if footprint.intersection(reserved_points):
            return False

        # Lightweight unit placement precheck against the current mutable unit mask.
        for placement, point in self._placement_points(spec.unit_tiles, anchor, transform):
            status = self.map_manager.base_placer._check_placement(  # type: ignore[attr-defined]
                self.unit_point_collection,
                point,
                placement.obj_type,
                placement.margin,
            )
            if status != CheckPlacementReturnTypes.SUCCESS:
                return False
        return True

    def stamp(
        self,
        spec: PrefabSpec,
        anchor: Point,
        transform: str = "identity",
        reserved_points: set[Point] | None = None,
    ) -> StampResult:
        reserved_points = reserved_points or set()
        if not self.can_stamp(spec, anchor, transform, reserved_points):
            return StampResult(False, set(), set(), set(), set())

        aoe_map = self.map_manager.get_map()
        reserved = self._mask_points(spec.footprint_mask + spec.reserved_mask, anchor, transform)
        terrain_pts: set[Point] = set()
        decor_pts: set[Point] = set()
        unit_pts: set[Point] = set()

        for placement, point in self._placement_points(spec.terrain_tiles, anchor, transform):
            if point in self.surface_allowed_points:
                aoe_map.set_point(point, placement.obj_type, MapLayerType.TERRAIN, placement.player_id)
                terrain_pts.add(point)

        for placement, point in self._placement_points(spec.decor_tiles, anchor, transform):
            if point in self.surface_allowed_points:
                aoe_map.set_point(point, placement.obj_type, MapLayerType.DECOR, placement.player_id)
                decor_pts.add(point)

        for placement, point in self._placement_points(spec.unit_tiles, anchor, transform):
            # We already prechecked; stamp deterministically.
            self.map_manager.base_placer.place_if_possible(
                PlaceIfPossibleConfig(
                    point_collection=self.unit_point_collection,
                    map_layer_type=placement.layer,
                    obj_type=placement.obj_type,
                    starting_point=point,
                    player_id=placement.player_id,
                    margin=placement.margin,
                )
            )
            unit_pts.add(point)

        return StampResult(True, reserved, unit_pts, terrain_pts, decor_pts)

