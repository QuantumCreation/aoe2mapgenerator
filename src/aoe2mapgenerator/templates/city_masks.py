"""Mask construction helpers for deterministic CITY ward layout."""

from __future__ import annotations

from dataclasses import dataclass

from aoe2mapgenerator.templates.city_geometry import SECTOR_ORDER, sector_for_point, to_point_collection
from aoe2mapgenerator.templates.city_layout_plan import CityLayoutPlan
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection

Point = tuple[int, int]


def _bbox(points: set[Point]) -> tuple[int, int, int, int] | None:
    if not points:
        return None
    rs = [p[0] for p in points]
    cs = [p[1] for p in points]
    return (min(rs), min(cs), max(rs), max(cs))


def _center(points: set[Point], fallback: Point) -> Point:
    if not points:
        return fallback
    return (sum(p[0] for p in points) // len(points), sum(p[1] for p in points) // len(points))


@dataclass(frozen=True)
class CityRingRadii:
    radius_wall: int
    radius_patrol_ring: int
    radius_main_ring: int
    radius_inner_ring: int
    radius_outer_ward: int
    radius_central_plaza: int
    radius_palace_precinct: int
    radius_wall_inner_clear: int


class CityMaskBuilder:
    """Builds city masks from selected points, ring radii, and reserved areas."""

    @staticmethod
    def build_ward_masks(
        selected_points: set[Point],
        center: Point,
        radius_inner: int,
        radius_outer: int,
        reserved_points: set[Point],
    ) -> dict[str, PointCollection]:
        inner_sq = radius_inner * radius_inner
        outer_sq = radius_outer * radius_outer
        cr, cc = center
        per_sector: dict[str, set[Point]] = {s: set() for s in SECTOR_ORDER}
        for r, c in selected_points:
            if (r, c) in reserved_points:
                continue
            dr = r - cr
            dc = c - cc
            d2 = dr * dr + dc * dc
            if d2 < inner_sq or d2 > outer_sq:
                continue
            per_sector[sector_for_point(center, (r, c))].add((r, c))
        return {sector: to_point_collection(points) for sector, points in per_sector.items()}

    @staticmethod
    def build_plan(
        center: Point,
        rings: CityRingRadii,
        selected_points: set[Point],
        interior_points: set[Point],
        core_reserved: set[Point],
        road_masks: dict[str, set[Point]],
        plaza_masks: dict[str, set[Point]],
    ) -> CityLayoutPlan:
        reserved_points = set(core_reserved)
        for pts in road_masks.values():
            reserved_points.update(pts)
        for pts in plaza_masks.values():
            reserved_points.update(pts)
        ward_masks = CityMaskBuilder.build_ward_masks(
            selected_points=selected_points,
            center=center,
            radius_inner=rings.radius_inner_ring,
            radius_outer=rings.radius_outer_ward,
            reserved_points=reserved_points,
        )
        # Add outer buffer wards (between outer ward and wall-clear band) to existing masks
        outer_buffer = CityMaskBuilder.build_ward_masks(
            selected_points=selected_points,
            center=center,
            radius_inner=rings.radius_outer_ward + 1,
            radius_outer=rings.radius_wall_inner_clear,
            reserved_points=reserved_points,
        )
        for sector in SECTOR_ORDER:
            combined = set(ward_masks[sector].get_point_list()) | set(outer_buffer[sector].get_point_list())
            ward_masks[sector] = to_point_collection(combined)

        plan = CityLayoutPlan(
            center=center,
            radius_wall=rings.radius_wall,
            radius_patrol_ring=rings.radius_patrol_ring,
            radius_main_ring=rings.radius_main_ring,
            radius_inner_ring=rings.radius_inner_ring,
            core_mask=to_point_collection(core_reserved),
            interior_mask=to_point_collection(interior_points),
            ward_masks=ward_masks,
            road_masks={k: to_point_collection(v) for k, v in road_masks.items()},
            plaza_masks={k: to_point_collection(v) for k, v in plaza_masks.items()},
        )

        military = set(ward_masks["N"].get_point_list()) | set(ward_masks["NE"].get_point_list())
        market = set(ward_masks["E"].get_point_list()) | set(ward_masks["SE"].get_point_list())
        village = (
            set(ward_masks["S"].get_point_list())
            | set(ward_masks["SW"].get_point_list())
            | set(ward_masks["W"].get_point_list())
            | set(ward_masks["NW"].get_point_list())
        )
        aggregates = {"military": military, "market": market, "village": village}
        plan.aggregate_trigger_areas = {
            name: bbox
            for name, pts in aggregates.items()
            if (bbox := _bbox(pts)) is not None
        }
        return plan

    @staticmethod
    def aggregate_centers(plan: CityLayoutPlan) -> dict[str, Point]:
        fallback = plan.center
        military = set(plan.ward_masks["N"].get_point_list()) | set(plan.ward_masks["NE"].get_point_list())
        market = set(plan.ward_masks["E"].get_point_list()) | set(plan.ward_masks["SE"].get_point_list())
        village = (
            set(plan.ward_masks["S"].get_point_list())
            | set(plan.ward_masks["SW"].get_point_list())
            | set(plan.ward_masks["W"].get_point_list())
            | set(plan.ward_masks["NW"].get_point_list())
        )
        return {
            "military": _center(military, fallback),
            "market": _center(market, fallback),
            "village": _center(village, fallback),
        }

