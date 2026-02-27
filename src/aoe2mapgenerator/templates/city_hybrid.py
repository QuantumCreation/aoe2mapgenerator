"""CITY template: deterministic hybrid-ward fortified city with actual gate-aligned roads."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.city_district_templates import DistrictPlacementResult
from aoe2mapgenerator.templates.city_geometry import (
    SECTOR_ORDER,
    SECTOR_VECTORS_FLOAT,
    SECTOR_VECTORS_INT,
    RoadCorridorPainter,
    capture_placed_gates,
    compute_gate_anchor_specs,
    distance_sq,
    filter_points_in_circle,
    nearest_point,
    sector_for_point,
    to_point_collection,
)
from aoe2mapgenerator.templates.city_layout_plan import CitySlotSpec
from aoe2mapgenerator.templates.city_masks import CityMaskBuilder, CityRingRadii
from aoe2mapgenerator.templates.city_prefab_stamper import CityPrefabStamper
from aoe2mapgenerator.templates.city_prefabs import get_city_prefab
from aoe2mapgenerator.templates.city_validation import CityLayoutValidator
from aoe2mapgenerator.templates.palace import PalaceTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.triggers.city_life import apply_city_life_triggers
from aoe2mapgenerator.units.placers.gate_utility import AdvancedWallPlacer
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceGroupsConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.units.wallgenerators.fort_shapes import FortShape, build_fort_shape

Point = tuple[int, int]
CITY_MIN_RADIUS = 28


@dataclass(frozen=True)
class CityPreset:
    """Preset controls for city scale and population intensity."""

    name: str
    default_radius: int
    shape: str
    military_scale: float
    market_scale: float
    village_scale: float
    greenery_scale: float
    road_scale: float
    enable_patrols: bool = True


CITY_PRESETS: dict[str, CityPreset] = {
    "compact": CityPreset(
        name="compact",
        default_radius=62,
        shape="octagon",
        military_scale=0.78,
        market_scale=0.80,
        village_scale=0.82,
        greenery_scale=0.72,
        road_scale=0.88,
    ),
    "balanced": CityPreset(
        name="balanced",
        default_radius=90,
        shape="octagon",
        military_scale=1.0,
        market_scale=1.0,
        village_scale=1.0,
        greenery_scale=1.0,
        road_scale=1.0,
    ),
    "mega_city": CityPreset(
        name="mega_city",
        default_radius=122,
        shape="octagon",
        military_scale=1.45,
        market_scale=1.40,
        village_scale=1.55,
        greenery_scale=1.35,
        road_scale=1.22,
    ),
    "mega": CityPreset(
        name="mega_city",
        default_radius=122,
        shape="octagon",
        military_scale=1.45,
        market_scale=1.40,
        village_scale=1.55,
        greenery_scale=1.35,
        road_scale=1.22,
    ),
}


def _resolve_city_preset(preset_name: str | None) -> CityPreset:
    if not preset_name:
        return CITY_PRESETS["balanced"]
    key = str(preset_name).strip().lower()
    if key not in CITY_PRESETS:
        valid = ", ".join(sorted(set(CITY_PRESETS) - {"mega"}))
        raise ValueError(f"Unknown city preset '{preset_name}'. Valid presets: {valid}, mega")
    return CITY_PRESETS[key]


def _normalize_requested_city_radius(requested_radius: Any, preset: CityPreset) -> int:
    """Normalize external size inputs for CITY.

    The backend UI still sends a generic template ``size`` (commonly ``12``) for CITY.
    The hybrid CITY layout requires a larger minimum radius, so treat undersized values
    as "use preset default" to preserve backwards compatibility for existing requests.
    """
    if not isinstance(requested_radius, (int, float)):
        return preset.default_radius
    radius = int(requested_radius)
    if radius <= 0:
        return preset.default_radius
    if radius < CITY_MIN_RADIUS:
        return preset.default_radius
    return radius


def _get_object_points(map_manager: IMapManager, obj_type, player_id: PlayerId) -> list[Point]:
    points = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(obj_type, player_id),
    )
    return list(points)


def _nearest_or_fallback(reference: Point, points: list[Point], fallback: Point) -> Point:
    if not points:
        return fallback
    return nearest_point(reference, points)


def _build_villager_targets(map_manager: IMapManager, village_center: Point, player_id: PlayerId) -> dict[str, Point]:
    farms = _get_object_points(map_manager, BuildingInfo.FARM, player_id)
    stones = _get_object_points(map_manager, OtherInfo.STONE_MINE, PlayerId.GAIA)
    golds = _get_object_points(map_manager, OtherInfo.GOLD_MINE, PlayerId.GAIA)
    forage = _get_object_points(map_manager, OtherInfo.FORAGE_BUSH, PlayerId.GAIA)

    fallback_farm = (village_center[0] + 6, village_center[1] + 5)
    fallback_stone = (village_center[0] - 10, village_center[1] + 3)
    fallback_gold = (village_center[0] + 10, village_center[1] - 4)
    fallback_forage = (village_center[0] - 5, village_center[1] - 6)

    return {
        "farm": _nearest_or_fallback(village_center, farms, fallback_farm),
        "stone_mine": _nearest_or_fallback(village_center, stones, fallback_stone),
        "gold_mine": _nearest_or_fallback(village_center, golds, fallback_gold),
        "forage": _nearest_or_fallback(village_center, forage, fallback_forage),
    }


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _compute_ring_radii(city_radius: int, include_palace: bool) -> CityRingRadii:
    r_wall = int(city_radius)
    r_wall_inner_clear = max(12, r_wall - 4)
    r_patrol_ring = max(8, round(r_wall - 9))
    r_outer_ward = max(12, round(r_wall * 0.78))
    r_main_ring = max(10, round(r_wall * 0.62))
    r_inner_ring = max(8, round(r_wall * 0.42))
    r_central_plaza = _clamp(round(r_wall * 0.15), 10, 20)
    r_palace_precinct = _clamp(round(r_wall * 0.24), 14, 30) if include_palace else 0
    return CityRingRadii(
        radius_wall=r_wall,
        radius_patrol_ring=r_patrol_ring,
        radius_main_ring=r_main_ring,
        radius_inner_ring=r_inner_ring,
        radius_outer_ward=r_outer_ward,
        radius_central_plaza=r_central_plaza,
        radius_palace_precinct=r_palace_precinct,
        radius_wall_inner_clear=r_wall_inner_clear,
    )


def _sector_point(center: Point, sector: str, radius: float) -> Point:
    vr, vc = SECTOR_VECTORS_FLOAT[sector]
    return (int(round(center[0] + vr * radius)), int(round(center[1] + vc * radius)))


def _perp_left(vec: Point) -> Point:
    return (-vec[1], vec[0])


def _offset_point(point: Point, vec: Point, scale: int) -> Point:
    return (point[0] + vec[0] * scale, point[1] + vec[1] * scale)


def _preflight_wall_fit(
    point_collection: PointCollection,
    center_point: Point,
    city_radius: int,
    shape: str,
    auto_shrink: bool,
) -> tuple[FortShape, int]:
    selected = set(point_collection.get_point_list())
    radius = city_radius
    min_radius = CITY_MIN_RADIUS
    while radius >= min_radius:
        try:
            fort_shape = build_fort_shape(shape, center_point, radius=radius)
        except Exception:
            fort_shape = build_fort_shape("octagon", center_point, radius=radius)
        wall_set = set(fort_shape.wall_points)
        if not wall_set:
            if not auto_shrink:
                break
            radius -= 4
            continue
        coverage = len(wall_set & selected) / max(1, len(wall_set))
        if coverage >= 0.98:
            return fort_shape, radius
        if not auto_shrink:
            break
        radius -= 4
    raise ValueError("CITY layout does not fit selected region")


def _place_corner_towers(
    map_manager: IMapManager,
    point_collection: PointCollection,
    corner_points: list[Point],
    player_id: PlayerId,
) -> None:
    for corner in corner_points:
        map_manager.base_placer.place_closest_to_point(
            PlaceClosestToPointConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.UNIT,
                obj_type=BuildingInfo.GUARD_TOWER,
                starting_point=corner,
                player_id=player_id,
                margin=1,
            )
        )


def _paint_major_roads(
    map_manager: IMapManager,
    center: Point,
    rings: CityRingRadii,
    selected_points: set[Point],
    gates,
    player_id: PlayerId,
) -> tuple[RoadCorridorPainter, dict[str, set[Point]], dict[str, set[Point]], set[Point]]:
    painter = RoadCorridorPainter(map_manager, allowed_points=selected_points, player_id=player_id)
    road_masks: dict[str, set[Point]] = {}
    plaza_masks: dict[str, set[Point]] = {}

    for gate in gates:
        plaza_masks[f"gate_{gate.sector}"] = painter.paint_circle_patch(
            gate.inner_approach_tile, radius=2, terrain_obj=TerrainId.ROAD, key=f"gate_plaza_{gate.sector}"
        )

    plaza_masks["center"] = painter.paint_circle_patch(
        center, radius=max(2, rings.radius_central_plaza // 3), terrain_obj=TerrainId.ROAD, key="central_plaza_seed"
    )

    patrol_points = [_sector_point(center, sector, rings.radius_patrol_ring) for sector in SECTOR_ORDER]
    patrol_points.append(patrol_points[0])
    road_masks["patrol_ring"] = painter.paint_polyline(patrol_points, TerrainId.ROAD, width=2, key="patrol_ring")

    main_ring_points = [_sector_point(center, sector, rings.radius_main_ring) for sector in SECTOR_ORDER]
    main_ring_points.append(main_ring_points[0])
    road_masks["main_ring"] = painter.paint_polyline(main_ring_points, TerrainId.ROAD, width=2, key="main_ring")

    road_masks["cardinal_trunks"] = set()
    road_masks["diag_connectors"] = set()
    for sector in ("N", "E", "S", "W"):
        rp = _sector_point(center, sector, rings.radius_main_ring)
        road_masks["cardinal_trunks"].update(
            painter.paint_polyline([center, rp], TerrainId.ROAD, width=3, key=f"trunk_{sector}")
        )
    for sector in ("NE", "SE", "SW", "NW"):
        rp = _sector_point(center, sector, rings.radius_main_ring)
        road_masks["diag_connectors"].update(
            painter.paint_polyline([center, rp], TerrainId.ROAD, width=2, key=f"diag_{sector}")
        )

    road_masks["gate_avenues"] = set()
    for gate in gates:
        ring_point = _sector_point(center, gate.sector, rings.radius_main_ring)
        width = 3 if gate.sector in {"N", "E", "S", "W"} else 2
        road_masks["gate_avenues"].update(
            painter.paint_polyline(
                [gate.inner_approach_tile, ring_point, center],
                TerrainId.ROAD,
                width=width,
                key=f"gate_avenue_{gate.sector}",
            )
        )

    all_road_points: set[Point] = set()
    for pts in road_masks.values():
        all_road_points.update(pts)
    for pts in plaza_masks.values():
        all_road_points.update(pts)
    return painter, road_masks, plaza_masks, all_road_points


def _repair_missing_gates(
    map_manager: IMapManager,
    gate_type: GateType,
    player_id: PlayerId,
    wall_intersection: PointCollection,
    wall_points: list[Point],
    center_point: Point,
    gate_specs,
) -> list:
    """City-local deterministic repair pass for missing gate sectors."""
    current = capture_placed_gates(map_manager, gate_type, center_point, player_id)
    existing_sectors = {g.sector for g in current}
    missing_specs = [spec for spec in gate_specs if spec.sector not in existing_sectors]
    if not missing_specs:
        return current

    # Rebuild a fresh candidate wall collection, then remove already-used gate footprint tiles.
    wall_candidate = to_point_collection(set(wall_intersection.get_point_list()) & set(wall_points))
    for gate in current:
        for point in gate.footprint_tiles:
            wall_candidate.remove_point(point)

    for spec in missing_specs:
        # Internal helper is deterministic given our target anchor and candidate wall set.
        map_manager.gate_placer._place_gate_closest_to_point(  # type: ignore[attr-defined]
            point_collection=wall_candidate,
            map_layer_type=MapLayerType.UNIT,
            gate_type=gate_type,
            goal_placement_point=spec.target_wall_anchor,
            player_id=player_id,
        )
    return capture_placed_gates(map_manager, gate_type, center_point, player_id)


def _gatehouse_transform_for_sector(sector: str) -> str:
    return {
        "N": "identity",
        "E": "rot90",
        "S": "rot180",
        "W": "rot270",
        "NE": "rot90",
        "SE": "rot180",
        "SW": "rot270",
        "NW": "identity",
    }[sector]


def _place_gatehouses(
    map_manager: IMapManager,
    stamper: CityPrefabStamper,
    gates,
    reserved_unit_points: set[Point],
) -> set[Point]:
    new_reserved: set[Point] = set()
    for gate in gates:
        spec_name = "GatehouseCardinalPrefab" if gate.sector in {"N", "E", "S", "W"} else "GatehouseDiagonalPrefab"
        spec = get_city_prefab(spec_name)
        inward_vec = tuple(-v for v in SECTOR_VECTORS_INT[gate.sector])
        anchor = _offset_point(gate.inner_approach_tile, inward_vec, 2)
        if spec_name == "GatehouseCardinalPrefab":
            lateral = _perp_left(inward_vec)
            anchor = _offset_point(anchor, lateral, -2)
        result = stamper.stamp(
            spec,
            anchor=anchor,
            transform=_gatehouse_transform_for_sector(gate.sector),
            reserved_points=reserved_unit_points | new_reserved,
        )
        if result.success:
            new_reserved.update(result.reserved_points)
        else:
            for tower_anchor in (
                _offset_point(gate.inner_approach_tile, _perp_left(inward_vec), 3),
                _offset_point(gate.inner_approach_tile, _perp_left(inward_vec), -3),
            ):
                map_manager.base_placer.place_closest_to_point(
                    PlaceClosestToPointConfig(
                        point_collection=stamper.unit_point_collection.copy(),
                        map_layer_type=MapLayerType.UNIT,
                        obj_type=BuildingInfo.GUARD_TOWER,
                        starting_point=tower_anchor,
                        player_id=PlayerId.ONE,
                        margin=1,
                    )
                )
    return new_reserved


def _slot_orientation(sector: str) -> str:
    return {
        "N": "identity",
        "NE": "identity",
        "E": "rot90",
        "SE": "rot90",
        "S": "rot180",
        "SW": "rot180",
        "W": "rot270",
        "NW": "rot270",
    }[sector]


def _slot_anchor(center: Point, sector: str, radial: float, lateral: int = 0) -> Point:
    base = _sector_point(center, sector, radial)
    inward = tuple(-v for v in SECTOR_VECTORS_INT[sector])
    lateral_vec = _perp_left(inward)
    return _offset_point(base, lateral_vec, lateral)


def _build_slot_specs(center: Point, rings: CityRingRadii, preset: CityPreset, include_palace: bool) -> list[CitySlotSpec]:
    slots: list[CitySlotSpec] = []

    def add(slot_id: str, ward: str, radial: float, allowed: tuple[str, ...], lateral: int = 0, required: bool = True) -> None:
        slots.append(
            CitySlotSpec(
                slot_id=slot_id,
                ward=ward,
                anchor=_slot_anchor(center, ward, radial, lateral),
                orientation=_slot_orientation(ward),
                allowed_prefabs=allowed,
                required=required,
                variant_key=slot_id,
            )
        )

    add("N_military_1", "N", rings.radius_main_ring + 6, ("MilitaryYardPrefab_A",))
    add("N_military_2", "N", rings.radius_outer_ward - 8, ("MilitaryYardPrefab_B",), lateral=7)
    add("N_guard_pocket", "N", rings.radius_outer_ward - 12, ("GardenPocketPrefab_B",), lateral=-8, required=False)

    add("NE_siege", "NE", rings.radius_main_ring + 8, ("SiegeYardPrefab",))
    add("NE_training", "NE", rings.radius_outer_ward - 10, ("MilitaryYardPrefab_A", "MilitaryYardPrefab_B"), lateral=7)
    add("NE_garden", "NE", rings.radius_outer_ward - 6, ("GardenPocketPrefab_A",), lateral=-7, required=False)

    add("E_market_core", "E", rings.radius_main_ring + (10 if include_palace else 4), ("MarketPlazaCorePrefab",))
    add("E_market_lane_1", "E", rings.radius_outer_ward - 8, ("MarketLanePrefab_A",), lateral=8)
    add("E_market_lane_2", "E", rings.radius_outer_ward - 12, ("MarketLanePrefab_B",), lateral=-8)

    add("SE_craft_1", "SE", rings.radius_main_ring + 8, ("MarketLanePrefab_A", "MarketLanePrefab_B"))
    add("SE_craft_2", "SE", rings.radius_outer_ward - 9, ("MarketLanePrefab_B",), lateral=7)
    add("SE_market_lane", "SE", rings.radius_outer_ward - 13, ("MarketLanePrefab_A",), lateral=-7, required=False)

    add("S_commons", "S", rings.radius_main_ring + 5, ("TownCommonsPrefab",))
    add("S_farm_1", "S", rings.radius_outer_ward - 9, ("FarmsteadBlockPrefab",), lateral=10)
    add("S_farm_2", "S", rings.radius_outer_ward - 13, ("FarmsteadBlockPrefab",), lateral=-10)

    add("SW_res_1", "SW", rings.radius_main_ring + 6, ("ResidentialCourtyardPrefab_A", "ResidentialCourtyardPrefab_B"))
    add("SW_res_2", "SW", rings.radius_outer_ward - 8, ("ResidentialCourtyardPrefab_C",), lateral=8)
    add("SW_orchard", "SW", rings.radius_outer_ward - 12, ("GardenPocketPrefab_A",), lateral=-8, required=False)

    add("W_res_1", "W", rings.radius_main_ring + 6, ("ResidentialCourtyardPrefab_A",), lateral=8)
    add("W_res_2", "W", rings.radius_main_ring + 11, ("ResidentialCourtyardPrefab_B",), lateral=-8)
    add("W_res_3", "W", rings.radius_outer_ward - 7, ("ResidentialCourtyardPrefab_C",))
    add("W_street_garden", "W", rings.radius_outer_ward - 12, ("GardenPocketPrefab_B",), lateral=12, required=False)

    add("NW_noble", "NW", rings.radius_main_ring + 6, ("NobleCourtyardPrefab",))
    add("NW_res", "NW", rings.radius_outer_ward - 8, ("ResidentialCourtyardPrefab_A",), lateral=8)
    add("NW_guard_garden", "NW", rings.radius_outer_ward - 12, ("GardenPocketPrefab_A",), lateral=-8, required=False)

    if preset.name == "compact":
        compact_drop = {"W_res_3", "N_guard_pocket", "SE_market_lane"}
        slots = [s for s in slots if s.slot_id not in compact_drop]
    elif preset.name == "mega_city":
        add("N_extra_yard", "N", rings.radius_main_ring + 14, ("MilitaryYardPrefab_A",), lateral=-8, required=False)
        add("E_extra_lane", "E", rings.radius_main_ring + 14, ("MarketLanePrefab_B",), lateral=14, required=False)
        add("W_extra_res", "W", rings.radius_outer_ward - 10, ("ResidentialCourtyardPrefab_B",), lateral=-14, required=False)
        add("SW_extra_farm", "SW", rings.radius_outer_ward - 10, ("FarmsteadBlockPrefab",), lateral=12, required=False)

    return slots


def _place_ward_prefabs(
    map_manager: IMapManager,
    city_unit_available: PointCollection,
    surface_allowed: set[Point],
    slots: list[CitySlotSpec],
    reserved_unit_points: set[Point],
    rng: random.Random,
) -> set[Point]:
    stamper = CityPrefabStamper(map_manager, city_unit_available, surface_allowed)
    all_reserved = set(reserved_unit_points)
    for slot in slots:
        # Seeded variant selection affects only which prefab in an allowed family is chosen.
        candidates = list(slot.allowed_prefabs)
        if len(candidates) > 1:
            first = rng.randrange(len(candidates))
            candidates = [candidates[first]] + [p for i, p in enumerate(candidates) if i != first]

        transforms = [slot.orientation, "identity", "rot90", "rot180", "rot270", "mirror"]
        success = False
        for candidate in candidates:
            spec = get_city_prefab(candidate)
            for transform in transforms:
                if transform not in spec.allowed_transforms:
                    continue
                result = stamper.stamp(spec, anchor=slot.anchor, transform=transform, reserved_points=all_reserved)
                if result.success:
                    all_reserved.update(result.reserved_points)
                    success = True
                    break
            if success:
                break
        if not success and slot.required:
            for fallback in ("GardenPocketPrefab_A", "GardenPocketPrefab_B"):
                spec = get_city_prefab(fallback)
                result = stamper.stamp(spec, anchor=slot.anchor, transform="identity", reserved_points=all_reserved)
                if result.success:
                    all_reserved.update(result.reserved_points)
                    success = True
                    break
    return all_reserved


def _place_corner_groves(
    map_manager: IMapManager,
    city_unit_available: PointCollection,
    surface_allowed: set[Point],
    center: Point,
    corner_points: list[Point],
    reserved_unit_points: set[Point],
) -> set[Point]:
    stamper = CityPrefabStamper(map_manager, city_unit_available, surface_allowed)
    reserved = set(reserved_unit_points)
    for corner in corner_points:
        sector = sector_for_point(center, corner)
        inward = tuple(-v for v in SECTOR_VECTORS_INT[sector])
        anchor = _offset_point(corner, inward, 8)
        prefab_name = "GardenPocketPrefab_B" if sector in {"N", "NE"} else "GardenPocketPrefab_A"
        result = stamper.stamp(get_city_prefab(prefab_name), anchor=anchor, transform="identity", reserved_points=reserved)
        if result.success:
            reserved.update(result.reserved_points)
    return reserved


def _place_street_tree_strips(
    map_manager: IMapManager,
    city_unit_available: PointCollection,
    surface_allowed: set[Point],
    center: Point,
    rings: CityRingRadii,
    preset: CityPreset,
    reserved_unit_points: set[Point],
) -> set[Point]:
    stamper = CityPrefabStamper(map_manager, city_unit_available, surface_allowed)
    reserved = set(reserved_unit_points)
    interval = 7 if preset.name == "compact" else (5 if preset.name == "mega_city" else 6)
    spec = get_city_prefab("StreetTreeStripPrefab")
    for sector in ("N", "S", "E", "W"):
        inward = tuple(-v for v in SECTOR_VECTORS_INT[sector])
        lateral = _perp_left(inward)
        base = _sector_point(center, sector, rings.radius_main_ring + 4)
        transform = "rot90" if sector in {"E", "W"} else "identity"
        for step in range(-2, 3):
            anchor = _offset_point(base, lateral, step * interval)
            anchor = _offset_point(anchor, inward, 2)
            result = stamper.stamp(spec, anchor=anchor, transform=transform, reserved_points=reserved)
            if result.success:
                reserved.update(result.reserved_points)
    return reserved


def _place_minor_connectors(
    painter: RoadCorridorPainter,
    center: Point,
    slots: list[CitySlotSpec],
    gates,
    rings: CityRingRadii,
    road_masks: dict[str, set[Point]],
) -> set[Point]:
    minor: set[Point] = set()
    key_targets = [_sector_point(center, sector, rings.radius_main_ring) for sector in SECTOR_ORDER]
    key_targets.extend([g.inner_approach_tile for g in gates])
    for slot in slots:
        target = nearest_point(slot.anchor, key_targets)
        minor.update(painter.paint_polyline([slot.anchor, target], TerrainId.DIRT_1, width=1, key=f"minor_{slot.slot_id}"))
    road_masks["minor_connectors"] = minor
    return minor


def _place_precise_resources_and_fillers(
    map_manager: IMapManager,
    plan,
    city_unit_available: PointCollection,
    player_id: PlayerId,
    rng: random.Random,
    preset: CityPreset,
) -> None:
    centers = CityMaskBuilder.aggregate_centers(plan)
    v_center = centers["village"]
    anchors = [
        (OtherInfo.STONE_MINE, PlayerId.GAIA, (v_center[0] - 8, v_center[1] + 3)),
        (OtherInfo.GOLD_MINE, PlayerId.GAIA, (v_center[0] + 8, v_center[1] - 3)),
        (OtherInfo.FORAGE_BUSH, PlayerId.GAIA, (v_center[0] - 5, v_center[1] - 6)),
        (BuildingInfo.FARM, player_id, (v_center[0] + 6, v_center[1] + 4)),
    ]
    for obj, owner, anchor in anchors:
        map_manager.base_placer.place_closest_to_point(
            PlaceClosestToPointConfig(
                point_collection=city_unit_available.copy(),
                map_layer_type=MapLayerType.UNIT,
                obj_type=obj,
                starting_point=anchor,
                player_id=owner,
                margin=0,
            )
        )

    # Guarantee landmark/unit anchors expected by tests and city-life logic.
    guaranteed = [
        (plan.ward_masks["NE"], BuildingInfo.SIEGE_WORKSHOP, player_id, centers["military"]),
        (plan.ward_masks["N"], UnitInfo.KNIGHT, player_id, centers["military"]),
        (plan.ward_masks["E"], BuildingInfo.MARKET, player_id, centers["market"]),
        (plan.ward_masks["E"], UnitInfo.TRADE_CART_FULL, player_id, centers["market"]),
        (plan.ward_masks["W"], BuildingInfo.HOUSE, player_id, centers["village"]),
        (plan.ward_masks["SW"], BuildingInfo.HOUSE, player_id, centers["village"]),
        (plan.ward_masks["S"], UnitInfo.VILLAGER_MALE, player_id, centers["village"]),
    ]
    for collection, obj, owner, anchor in guaranteed:
        if not collection.get_point_list():
            continue
        map_manager.base_placer.place_closest_to_point(
            PlaceClosestToPointConfig(
                point_collection=collection.copy(),
                map_layer_type=MapLayerType.UNIT,
                obj_type=obj,
                starting_point=anchor,
                player_id=owner,
                margin=0 if "VILLAGER" in getattr(obj, "_name_", "") else 1 if hasattr(obj, "_name_") and obj._name_ in {"MARKET", "SIEGE_WORKSHOP"} else 0,
            )
        )

    filler_specs = [
        (plan.ward_masks["N"], UnitInfo.SPEARMAN, player_id, max(1, int(round(2 * preset.military_scale))), 2),
        (plan.ward_masks["NE"], UnitInfo.ARCHER, player_id, max(1, int(round(2 * preset.military_scale))), 2),
        (plan.ward_masks["E"], UnitInfo.TRADE_CART_EMPTY, player_id, max(1, int(round(2 * preset.market_scale))), 1),
        (plan.ward_masks["SE"], UnitInfo.CART, player_id, max(1, int(round(2 * preset.market_scale))), 1),
        (plan.ward_masks["W"], UnitInfo.VILLAGER_MALE, player_id, max(1, int(round(2 * preset.village_scale))), 2),
        (plan.ward_masks["SW"], UnitInfo.VILLAGER_FEMALE, player_id, max(1, int(round(2 * preset.village_scale))), 2),
    ]
    random_state = random.getstate()
    try:
        random.seed(rng.randint(0, 2**31 - 1))
        for collection, unit, owner, groups, group_size in filler_specs:
            if not collection.get_point_list():
                continue
            map_manager.group_placer.place_groups(
                PlaceGroupsConfig(
                    point_collection=collection.copy(),
                    map_layer_type=MapLayerType.UNIT,
                    object_type=unit,
                    player_id=owner,
                    groups=groups,
                    group_size=group_size,
                    clumping=3,
                )
            )
    finally:
        random.setstate(random_state)


def _district_results_from_plan(plan) -> list[DistrictPlacementResult]:
    centers = CityMaskBuilder.aggregate_centers(plan)
    return [
        DistrictPlacementResult("military", centers["military"], plan.aggregate_trigger_areas.get("military")),
        DistrictPlacementResult("market", centers["market"], plan.aggregate_trigger_areas.get("market")),
        DistrictPlacementResult("village", centers["village"], plan.aggregate_trigger_areas.get("village")),
    ]


@register_template(TemplateType.CITY)
class CityTemplate(AbstractTemplate):
    """Build a deterministic hybrid-ward fortified city using exact-prefab slots."""

    def __init__(self, name: str = "City", description: str = "Creates a full fortified city"):
        self.name = name
        self.description = description

    @staticmethod
    def generate(map_manager: IMapManager, point_collection: PointCollection, *args, **kwargs) -> PointCollection:
        preset_name = kwargs.get("preset", "balanced")
        preset = _resolve_city_preset(preset_name)
        center_point: Point = kwargs.get("center_point", point_collection.get_average_point_position())
        city_radius = kwargs.get("city_radius")
        if city_radius is None:
            size_from_kwargs = kwargs.get("size", 0)
            city_radius = _normalize_requested_city_radius(size_from_kwargs, preset)
        else:
            city_radius = _normalize_requested_city_radius(city_radius, preset)

        player_id: PlayerId = kwargs.get("player_id", PlayerId.ONE)
        gate_type: GateType = kwargs.get("gate_type", GateType.CITY_GATE)
        shape: str = kwargs.get("shape", preset.shape)
        enable_patrols: bool = kwargs.get("enable_patrols", preset.enable_patrols)
        enable_city_life: bool = kwargs.get("enable_city_life", enable_patrols)
        include_palace: bool = kwargs.get("include_palace", True)
        auto_shrink_to_fit: bool = bool(kwargs.get("auto_shrink_to_fit", kwargs.get("city_auto_shrink_to_fit", True)))
        seed = kwargs.get("seed")

        random_state = None
        rng = random.Random()
        if seed is not None:
            random_state = random.getstate()
            random.seed(seed)
            rng = random.Random(seed)

        try:
            fort_shape, resolved_radius = _preflight_wall_fit(
                point_collection=point_collection,
                center_point=center_point,
                city_radius=int(city_radius),
                shape=shape,
                auto_shrink=auto_shrink_to_fit,
            )
            wall_points = fort_shape.wall_points
            corner_points = fort_shape.corner_points
            rings = _compute_ring_radii(resolved_radius, include_palace=include_palace)

            selected_points = set(point_collection.get_point_list())
            interior_points = filter_points_in_circle(selected_points, center_point, rings.radius_wall_inner_clear)
            if not interior_points:
                raise ValueError("CITY layout does not fit selected region")

            wall_placer = AdvancedWallPlacer(map_manager.get_map())
            wall_type = gate_type.get_building_info_wall()
            city_wall_collection = map_manager.point_manager.add_point_collection("city_wall_points", wall_points, True)
            wall_intersection = point_collection.intersect(city_wall_collection)
            wall_intersection_editable = wall_intersection.copy()

            wall_placer.place_wall_points(map_manager, point_collection, wall_points, wall_type, player_id)
            if fort_shape.use_eight_side_gates:
                map_manager.gate_placer.place_gate_on_eight_sides(
                    point_collection=wall_intersection_editable,
                    map_layer_type=MapLayerType.UNIT,
                    gate_type=gate_type,
                    player_id=player_id,
                )
            else:
                map_manager.gate_placer.place_gate_on_four_sides(
                    point_collection=wall_intersection_editable,
                    map_layer_type=MapLayerType.UNIT,
                    gate_type=gate_type,
                    player_id=player_id,
                )

            gate_specs = compute_gate_anchor_specs(wall_points, center_point)
            actual_gates = capture_placed_gates(map_manager, gate_type, center_point, player_id)
            expected_gate_count = 8 if fort_shape.use_eight_side_gates else 4
            if fort_shape.use_eight_side_gates and len(actual_gates) < expected_gate_count:
                actual_gates = _repair_missing_gates(
                    map_manager=map_manager,
                    gate_type=gate_type,
                    player_id=player_id,
                    wall_intersection=wall_intersection,
                    wall_points=wall_points,
                    center_point=center_point,
                    gate_specs=gate_specs,
                )

            gate_validation = CityLayoutValidator.validate_gate_count(actual_gates, expected=expected_gate_count)
            if not gate_validation.ok:
                raise ValueError(f"CITY gate placement invalid: {'; '.join(gate_validation.errors)}")

            _place_corner_towers(map_manager, point_collection, corner_points, player_id)

            painter, road_masks, plaza_masks, all_road_points = _paint_major_roads(
                map_manager=map_manager,
                center=center_point,
                rings=rings,
                selected_points=selected_points,
                gates=actual_gates,
                player_id=player_id,
            )

            core_reserved = filter_points_in_circle(
                selected_points,
                center_point,
                rings.radius_palace_precinct if include_palace else rings.radius_central_plaza,
            )
            center_ring_pts = [_sector_point(center_point, s, max(4, rings.radius_central_plaza)) for s in SECTOR_ORDER]
            center_ring_pts.append(center_ring_pts[0])
            road_masks["center_ring"] = painter.paint_polyline(center_ring_pts, TerrainId.ROAD, width=2, key="center_ring")
            all_road_points.update(road_masks["center_ring"])

            plan = CityMaskBuilder.build_plan(
                center=center_point,
                rings=rings,
                selected_points=selected_points,
                interior_points=interior_points,
                core_reserved=core_reserved,
                road_masks=road_masks,
                plaza_masks=plaza_masks,
            )
            plan.gate_specs = gate_specs
            plan.slot_specs = _build_slot_specs(center_point, rings, preset, include_palace)

            ward_validation = CityLayoutValidator.validate_wards(plan, minimum_tiles=15 if preset.name == "compact" else 25)
            if not ward_validation.ok:
                raise ValueError(f"CITY ward layout invalid: {'; '.join(ward_validation.errors)}")

            palace_center: Point | None = None
            if include_palace:
                PalaceTemplate.generate(
                    map_manager=map_manager,
                    point_collection=to_point_collection(interior_points).copy(),
                    center_point=center_point,
                    radius=rings.radius_palace_precinct,
                    player_id=player_id,
                    gate_type=GateType.FORTIFIED_GATE,
                    include_moat=kwargs.get("palace_include_moat", True),
                )
                palace_center = center_point
            else:
                core_unit_available = to_point_collection(interior_points - all_road_points)
                CityPrefabStamper(map_manager, core_unit_available, selected_points).stamp(
                    get_city_prefab("MarketPlazaCorePrefab"), center_point, "identity", reserved_points=set()
                )

            reserved_unit_points = set(all_road_points) | set(core_reserved)
            city_unit_available = to_point_collection(interior_points - reserved_unit_points)

            gatehouse_reserved = _place_gatehouses(
                map_manager,
                CityPrefabStamper(map_manager, city_unit_available, selected_points),
                actual_gates,
                reserved_unit_points,
            )
            reserved_unit_points.update(gatehouse_reserved)

            plan.slot_specs.sort(key=lambda s: s.slot_id)
            reserved_unit_points = _place_ward_prefabs(
                map_manager=map_manager,
                city_unit_available=city_unit_available,
                surface_allowed=selected_points,
                slots=plan.slot_specs,
                reserved_unit_points=reserved_unit_points,
                rng=rng,
            )

            reserved_unit_points = _place_corner_groves(
                map_manager,
                city_unit_available,
                selected_points,
                center_point,
                corner_points,
                reserved_unit_points,
            )
            reserved_unit_points = _place_street_tree_strips(
                map_manager,
                city_unit_available,
                selected_points,
                center_point,
                rings,
                preset,
                reserved_unit_points,
            )

            minor = _place_minor_connectors(
                painter=painter,
                center=center_point,
                slots=plan.slot_specs,
                gates=actual_gates,
                rings=rings,
                road_masks=road_masks,
            )
            all_road_points.update(minor)

            _place_precise_resources_and_fillers(
                map_manager=map_manager,
                plan=plan,
                city_unit_available=city_unit_available,
                player_id=player_id,
                rng=rng,
                preset=preset,
            )

            gate_road_validation = CityLayoutValidator.validate_gate_road_reach(actual_gates, all_road_points)
            if not gate_road_validation.ok:
                raise ValueError(f"CITY gate-road alignment invalid: {'; '.join(gate_road_validation.errors)}")

            district_results = _district_results_from_plan(plan)
            if enable_city_life:
                villager_targets = _build_villager_targets(
                    map_manager=map_manager,
                    village_center=next((d.center for d in district_results if d.name == "village"), center_point),
                    player_id=player_id,
                )
                apply_city_life_triggers(
                    map_manager=map_manager,
                    district_results=district_results,
                    gate_points=[gate.gate_center_tile for gate in actual_gates],
                    city_center=center_point,
                    player_id=player_id,
                    villager_targets=villager_targets,
                    palace_center=palace_center,
                )

            setattr(
                map_manager,
                "_last_city_debug",
                {
                    "center": center_point,
                    "resolved_radius": resolved_radius,
                    "gate_count": len(actual_gates),
                    "gate_sectors": [g.sector for g in actual_gates],
                    "gate_points": [g.gate_center_tile for g in actual_gates],
                    "inner_gate_approaches": [g.inner_approach_tile for g in actual_gates],
                    "road_point_count": len(all_road_points),
                    "road_points": sorted(all_road_points),
                    "ward_sizes": {k: len(v.get_point_list()) for k, v in plan.ward_masks.items()},
                    "aggregate_trigger_areas": dict(plan.aggregate_trigger_areas),
                },
            )

            return to_point_collection(interior_points)
        finally:
            if random_state is not None:
                random.setstate(random_state)
