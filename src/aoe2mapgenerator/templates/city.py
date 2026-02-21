"""City template: generates a large multi-district fortified city.

The city is composed from smaller district templates to keep behaviour modular:
- military district
- market district
- village district
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.city_district_templates import (
    CityMarketDistrictTemplate,
    CityMilitaryDistrictTemplate,
    CityVillageDistrictTemplate,
    DistrictPlacementResult,
)
from aoe2mapgenerator.templates.palace import PalaceTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.triggers.city_life import apply_city_life_triggers
from aoe2mapgenerator.units.placers.gate_utility import AdvancedWallPlacer
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceGroupsConfig,
    PlacePathConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.units.wallgenerators.fort_shapes import FortShape, build_fort_shape

Point = Tuple[int, int]


@dataclass(frozen=True)
class CityDistrictCollections:
    """Spatial partition used by CityTemplate."""

    interior: PointCollection
    market: PointCollection
    military: PointCollection
    village: PointCollection
    greenery: PointCollection


@dataclass(frozen=True)
class CityPreset:
    """Preset controls for city scale, shape, and population intensity."""

    name: str
    default_radius: int
    shape: str
    market_radius_fraction: float
    military_min_fraction: float
    military_max_fraction: float
    greenery_min_fraction: float
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
        market_radius_fraction=0.29,
        military_min_fraction=0.34,
        military_max_fraction=0.88,
        greenery_min_fraction=0.80,
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
        market_radius_fraction=0.33,
        military_min_fraction=0.30,
        military_max_fraction=0.92,
        greenery_min_fraction=0.74,
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
        market_radius_fraction=0.36,
        military_min_fraction=0.26,
        military_max_fraction=0.95,
        greenery_min_fraction=0.68,
        military_scale=1.45,
        market_scale=1.40,
        village_scale=1.55,
        greenery_scale=1.35,
        road_scale=1.22,
    ),
    # Alias for convenience.
    "mega": CityPreset(
        name="mega_city",
        default_radius=122,
        shape="octagon",
        market_radius_fraction=0.36,
        military_min_fraction=0.26,
        military_max_fraction=0.95,
        greenery_min_fraction=0.68,
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


def _distance_sq(a: Point, b: Point) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def _angle_deg(center: Point, point: Point) -> float:
    return (math.degrees(math.atan2(point[1] - center[1], point[0] - center[0])) + 360) % 360


def _in_sector(angle: float, start: float, end: float) -> bool:
    if start <= end:
        return start <= angle <= end
    return angle >= start or angle <= end


def _to_collection(points: set[Point]) -> PointCollection:
    collection = PointCollection()
    collection.add_points(points)
    return collection


def _nearest_point(reference: Point, candidates: List[Point]) -> Point:
    if not candidates:
        return reference
    return min(candidates, key=lambda point: _distance_sq(reference, point))


def _get_object_points(
    map_manager: IMapManager,
    obj_type,
    player_id: PlayerId,
) -> list[Point]:
    points = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(obj_type, player_id),
    )
    return list(points)


def _nearest_or_fallback(
    reference: Point,
    points: list[Point],
    fallback: Point,
) -> Point:
    if not points:
        return fallback
    return _nearest_point(reference, points)


def _build_villager_targets(
    map_manager: IMapManager,
    village_center: Point,
    player_id: PlayerId,
) -> dict[str, Point]:
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


def _build_city_district_collections(
    point_collection: PointCollection,
    center: Point,
    interior_radius: float,
    preset: CityPreset,
) -> CityDistrictCollections:
    cx, cy = center
    interior_radius_sq = interior_radius * interior_radius
    market_radius_sq = (interior_radius * preset.market_radius_fraction) ** 2
    military_min_sq = (interior_radius * preset.military_min_fraction) ** 2
    military_max_sq = (interior_radius * preset.military_max_fraction) ** 2
    greenery_min_sq = (interior_radius * preset.greenery_min_fraction) ** 2

    interior_points: set[Point] = set()
    market_points: set[Point] = set()
    military_points: set[Point] = set()
    greenery_points: set[Point] = set()

    for x, y in point_collection.get_point_list():
        dx = x - cx
        dy = y - cy
        dist_sq = dx * dx + dy * dy
        if dist_sq > interior_radius_sq:
            continue
        interior_points.add((x, y))
        if dist_sq <= market_radius_sq:
            market_points.add((x, y))
            continue

        angle = _angle_deg(center, (x, y))
        if military_min_sq <= dist_sq <= military_max_sq and _in_sector(angle, 300, 55):
            military_points.add((x, y))
            continue

        if dist_sq >= greenery_min_sq and _in_sector(angle, 160, 290):
            greenery_points.add((x, y))

    village_points = interior_points - market_points - military_points - greenery_points

    # If one partition came out too small, borrow from village to keep zones robust.
    if len(military_points) < 120 and village_points:
        transferable = {p for p in village_points if _in_sector(_angle_deg(center, p), 285, 70)}
        military_points.update(transferable)
        village_points.difference_update(transferable)
    if len(greenery_points) < 100 and village_points:
        transferable = {p for p in village_points if _distance_sq(p, center) >= greenery_min_sq}
        greenery_points.update(transferable)
        village_points.difference_update(transferable)

    # Final fallbacks to avoid empty district collections on constrained maps.
    if not market_points:
        market_points = set(interior_points)
    if not military_points:
        military_points = set(interior_points)
    if not village_points:
        village_points = set(interior_points)

    return CityDistrictCollections(
        interior=_to_collection(interior_points),
        market=_to_collection(market_points),
        military=_to_collection(military_points),
        village=_to_collection(village_points),
        greenery=_to_collection(greenery_points),
    )


def _place_city_roads(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center: Point,
    gate_points: List[Point],
    district_centers: List[Point],
    radius: float,
    player_id: PlayerId,
    road_scale: float = 1.0,
) -> None:
    # Main radial roads from city center to each gate.
    for gate_point in gate_points:
        map_manager.path_placer.create_path(
            PlacePathConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.ROAD,
                player_id=player_id,
                key_points=[center, gate_point],
                num_divisions=[2],
                random_shift_range=[1],
            )
        )

    # Inner ring road for circulation across districts.
    ring_radius = max(8.0, radius * (0.56 * road_scale))
    ring_points = []
    for angle in range(0, 360, 45):
        ring_points.append(
            (
                int(center[0] + ring_radius * math.cos(math.radians(angle))),
                int(center[1] + ring_radius * math.sin(math.radians(angle))),
            )
        )
    ring_points.append(ring_points[0])
    map_manager.path_placer.create_path(
        PlacePathConfig(
            point_collection=point_collection.copy(),
            map_layer_type=MapLayerType.TERRAIN,
            obj_type=TerrainId.ROAD,
            player_id=player_id,
            key_points=ring_points,
            num_divisions=[3],
            random_shift_range=[2],
        )
    )

    # Connect each district center to the city center and nearest gate.
    for district_center in district_centers:
        map_manager.path_placer.create_path(
            PlacePathConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.DIRT_1,
                player_id=player_id,
                key_points=[center, district_center],
                num_divisions=[2],
                random_shift_range=[1],
            )
        )

        nearest_gate = _nearest_point(district_center, gate_points)
        map_manager.path_placer.create_path(
            PlacePathConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.DIRT_1,
                player_id=player_id,
                key_points=[district_center, nearest_gate],
                num_divisions=[2],
                random_shift_range=[2],
            )
        )


def _place_gate_defenses(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center: Point,
    gate_points: List[Point],
    player_id: PlayerId,
) -> None:
    cx, cy = center
    for gate_x, gate_y in gate_points:
        dx = gate_x - cx
        dy = gate_y - cy
        distance = math.sqrt(dx * dx + dy * dy) or 1.0
        ux, uy = dx / distance, dy / distance
        px, py = -uy, ux

        inner_gate_point = (int(gate_x - 2 * ux), int(gate_y - 2 * uy))
        left_tower = (int(inner_gate_point[0] + 3 * px), int(inner_gate_point[1] + 3 * py))
        right_tower = (int(inner_gate_point[0] - 3 * px), int(inner_gate_point[1] - 3 * py))

        for tower_point in (left_tower, right_tower):
            map_manager.base_placer.place_closest_to_point(
                PlaceClosestToPointConfig(
                    point_collection=point_collection.copy(),
                    map_layer_type=MapLayerType.UNIT,
                    obj_type=BuildingInfo.GUARD_TOWER,
                    starting_point=tower_point,
                    player_id=player_id,
                    margin=1,
                )
            )

        guard_collection = point_collection.copy()
        guard_collection.filter_by_distance(inner_gate_point, distance=6, edit_in_place=True)
        for unit, group_size in ((UnitInfo.SPEARMAN, 4), (UnitInfo.ARCHER, 3)):
            map_manager.group_placer.place_groups(
                PlaceGroupsConfig(
                    point_collection=guard_collection.copy(),
                    map_layer_type=MapLayerType.UNIT,
                    object_type=unit,
                    player_id=player_id,
                    groups=2,
                    group_size=group_size,
                    clumping=3,
                )
            )


def _decorate_greenery(
    map_manager: IMapManager,
    greenery_points: PointCollection,
    all_city_points: PointCollection,
    greenery_scale: float = 1.0,
) -> None:
    tree_groups = max(1, int(round(4 * greenery_scale)))
    tree_group_size = max(3, int(round(6 * greenery_scale)))
    decor_groups = max(1, int(round(3 * greenery_scale)))
    decor_group_size = max(2, int(round(3 * greenery_scale)))

    if greenery_points.get_point_list():
        tree_types = [OtherInfo.TREE_OAK, OtherInfo.TREE_A, OtherInfo.TREE_B, OtherInfo.TREE_OAK_FOREST]
        for tree in tree_types:
            map_manager.group_placer.place_groups(
                PlaceGroupsConfig(
                    point_collection=greenery_points.copy(),
                    map_layer_type=MapLayerType.UNIT,
                    object_type=tree,
                    player_id=PlayerId.GAIA,
                    groups=tree_groups,
                    group_size=tree_group_size,
                    clumping=6,
                )
            )

    decor_types = [
        OtherInfo.BUSH_A,
        OtherInfo.BUSH_B,
        OtherInfo.FLOWERS_1,
        OtherInfo.FLOWERS_2,
        OtherInfo.ROCK_1,
        OtherInfo.ROCK_2,
    ]
    for decor in decor_types:
        map_manager.group_placer.place_groups(
            PlaceGroupsConfig(
                point_collection=all_city_points.copy(),
                map_layer_type=MapLayerType.DECOR,
                object_type=decor,
                player_id=PlayerId.GAIA,
                groups=decor_groups,
                group_size=decor_group_size,
                clumping=6,
            )
        )


@register_template(TemplateType.CITY)
class CityTemplate(AbstractTemplate):
    """Build a large city with military, market, and village districts."""

    def __init__(self, name: str = "City", description: str = "Creates a full fortified city"):
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        preset_name = kwargs.get("preset", "balanced")
        preset = _resolve_city_preset(preset_name)
        center_point: Point = kwargs.get(
            "center_point",
            point_collection.get_average_point_position(),
        )
        city_radius = kwargs.get("city_radius")
        if city_radius is None:
            size_from_kwargs = kwargs.get("size", 0)
            if isinstance(size_from_kwargs, (int, float)) and size_from_kwargs > 0:
                city_radius = int(size_from_kwargs)
            else:
                city_radius = preset.default_radius
        player_id: PlayerId = kwargs.get("player_id", PlayerId.ONE)
        gate_type: GateType = kwargs.get("gate_type", GateType.CITY_GATE)
        shape: str = kwargs.get("shape", preset.shape)
        enable_patrols: bool = kwargs.get("enable_patrols", preset.enable_patrols)
        enable_city_life: bool = kwargs.get("enable_city_life", enable_patrols)
        include_palace: bool = kwargs.get("include_palace", True)
        seed = kwargs.get("seed")

        random_state = None
        rng = random.Random()
        if seed is not None:
            random_state = random.getstate()
            random.seed(seed)
            rng = random.Random(seed)

        try:
            fort_shape: FortShape = build_fort_shape(shape, center_point, radius=city_radius)
            wall_points = fort_shape.wall_points
            corner_points = fort_shape.corner_points
            gate_points = fort_shape.gate_points
            interior_radius = max(12.0, fort_shape.inscribed_radius - 4.0)

            wall_placer = AdvancedWallPlacer(map_manager.get_map())
            wall_type = gate_type.get_building_info_wall()
            city_wall_collection = map_manager.point_manager.add_point_collection(
                "city_wall_points", wall_points, True
            )
            wall_intersection = point_collection.intersect(city_wall_collection)
            wall_intersection_editable = wall_intersection.copy()

            wall_placer.place_wall_points(
                map_manager,
                point_collection,
                wall_points,
                wall_type,
                player_id,
            )

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

            district_collections = _build_city_district_collections(
                point_collection=point_collection,
                center=center_point,
                interior_radius=interior_radius,
                preset=preset,
            )

            palace_center: Point | None = None
            if include_palace:
                palace_radius = kwargs.get(
                    "palace_radius",
                    max(14, min(30, int(interior_radius * 0.28))),
                )
                PalaceTemplate.generate(
                    map_manager=map_manager,
                    point_collection=district_collections.interior.copy(),
                    center_point=center_point,
                    radius=palace_radius,
                    player_id=player_id,
                    gate_type=GateType.FORTIFIED_GATE,
                    include_moat=kwargs.get("palace_include_moat", True),
                )
                palace_center = center_point

            military_result = CityMilitaryDistrictTemplate.generate(
                map_manager=map_manager,
                district_points=district_collections.military,
                fallback_center=center_point,
                city_radius=interior_radius,
                player_id=player_id,
                rng=rng,
                density_scale=kwargs.get("military_scale", preset.military_scale),
            )
            market_result = CityMarketDistrictTemplate.generate(
                map_manager=map_manager,
                district_points=district_collections.market,
                fallback_center=center_point,
                city_radius=interior_radius,
                player_id=player_id,
                rng=rng,
                density_scale=kwargs.get("market_scale", preset.market_scale),
            )
            village_result = CityVillageDistrictTemplate.generate(
                map_manager=map_manager,
                district_points=district_collections.village,
                fallback_center=center_point,
                city_radius=interior_radius,
                player_id=player_id,
                rng=rng,
                density_scale=kwargs.get("village_scale", preset.village_scale),
            )

            _place_city_roads(
                map_manager=map_manager,
                point_collection=district_collections.interior,
                center=center_point,
                gate_points=gate_points,
                district_centers=[military_result.center, market_result.center, village_result.center],
                radius=interior_radius,
                player_id=player_id,
                road_scale=kwargs.get("road_scale", preset.road_scale),
            )
            _place_gate_defenses(
                map_manager=map_manager,
                point_collection=district_collections.interior,
                center=center_point,
                gate_points=gate_points,
                player_id=player_id,
            )
            _decorate_greenery(
                map_manager=map_manager,
                greenery_points=district_collections.greenery,
                all_city_points=district_collections.interior,
                greenery_scale=kwargs.get("greenery_scale", preset.greenery_scale),
            )

            if enable_city_life:
                villager_targets = _build_villager_targets(
                    map_manager=map_manager,
                    village_center=village_result.center,
                    player_id=player_id,
                )
                apply_city_life_triggers(
                    map_manager=map_manager,
                    district_results=[military_result, market_result, village_result],
                    gate_points=gate_points,
                    city_center=center_point,
                    player_id=player_id,
                    villager_targets=villager_targets,
                    palace_center=palace_center,
                )

            return district_collections.interior
        finally:
            if random_state is not None:
                random.setstate(random_state)
