"""Modular district templates used by the high-level CityTemplate.

Each district template focuses on one region of the city:
- military
- market
- village / casual housing
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceGroupsConfig,
    PlacePathConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection

Point = Tuple[int, int]


@dataclass(frozen=True)
class DistrictPlacementResult:
    """Runtime metadata emitted by district templates."""

    name: str
    center: Point
    patrol_area: Optional[tuple[int, int, int, int]]


def _scaled_count(base: int, scale: float, minimum: int = 1) -> int:
    return max(minimum, int(round(base * max(0.1, scale))))


def _safe_average(collection: PointCollection, fallback: Point) -> Point:
    points = collection.get_point_list()
    if not points:
        return fallback
    return collection.get_average_point_position()


def _bounding_box(collection: PointCollection) -> Optional[tuple[int, int, int, int]]:
    points = collection.get_point_list()
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _subset_within_radius(
    collection: PointCollection, center: Point, radius: float
) -> PointCollection:
    cx, cy = center
    radius_sq = radius * radius
    subset = PointCollection()
    for x, y in collection.get_point_list():
        dx = x - cx
        dy = y - cy
        if dx * dx + dy * dy <= radius_sq:
            subset.add_point((x, y))
    return subset


def _place_building(
    map_manager: IMapManager,
    collection: PointCollection,
    start: Point,
    building: BuildingInfo,
    player_id: PlayerId,
    margin: int = 1,
) -> None:
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=collection.copy(),
            map_layer_type=MapLayerType.UNIT,
            obj_type=building,
            starting_point=start,
            player_id=player_id,
            margin=margin,
        )
    )


def _place_unit(
    map_manager: IMapManager,
    collection: PointCollection,
    start: Point,
    unit: UnitInfo,
    player_id: PlayerId,
) -> None:
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=collection.copy(),
            map_layer_type=MapLayerType.UNIT,
            obj_type=unit,
            starting_point=start,
            player_id=player_id,
            margin=0,
        )
    )


def _place_ring_buildings(
    map_manager: IMapManager,
    collection: PointCollection,
    center: Point,
    radius: float,
    buildings: list[BuildingInfo],
    player_id: PlayerId,
) -> None:
    if not buildings:
        return
    cx, cy = center
    step = 2 * math.pi / len(buildings)
    for idx, building in enumerate(buildings):
        angle = idx * step
        start = (int(cx + radius * math.cos(angle)), int(cy + radius * math.sin(angle)))
        _place_building(map_manager, collection, start, building, player_id)


def _place_group(
    map_manager: IMapManager,
    collection: PointCollection,
    layer: MapLayerType,
    obj,
    player_id: PlayerId,
    groups: int,
    group_size: int,
    clumping: int = 4,
    start_point: Optional[Point] = None,
) -> None:
    if not collection.get_point_list():
        return
    map_manager.group_placer.place_groups(
        PlaceGroupsConfig(
            point_collection=collection.copy(),
            map_layer_type=layer,
            object_type=obj,
            player_id=player_id,
            groups=groups,
            group_size=group_size,
            clumping=clumping,
            start_point=start_point,
        )
    )


class CityMilitaryDistrictTemplate:
    """Military district: production buildings, training units, and war decor."""

    @staticmethod
    def generate(
        map_manager: IMapManager,
        district_points: PointCollection,
        fallback_center: Point,
        city_radius: float,
        player_id: PlayerId,
        rng: random.Random,
        density_scale: float = 1.0,
    ) -> DistrictPlacementResult:
        center = _safe_average(district_points, fallback_center)
        if not district_points.get_point_list():
            return DistrictPlacementResult("military", center, None)

        ring_radius = max(7.0, city_radius * 0.14)
        _place_ring_buildings(
            map_manager=map_manager,
            collection=district_points,
            center=center,
            radius=ring_radius,
            buildings=[
                BuildingInfo.BARRACKS,
                BuildingInfo.SIEGE_WORKSHOP,
                BuildingInfo.STABLE,
                BuildingInfo.ARCHERY_RANGE,
                BuildingInfo.BLACKSMITH,
            ],
            player_id=player_id,
        )

        # Guarantee key military units exist for gameplay and testability.
        _place_unit(map_manager, district_points, center, UnitInfo.KNIGHT, player_id)
        _place_unit(
            map_manager,
            district_points,
            (center[0] + 2, center[1] - 1),
            UnitInfo.SPEARMAN,
            player_id,
        )

        troop_mix = [
            (UnitInfo.SPEARMAN, 4, 5),
            (UnitInfo.MAN_AT_ARMS, 3, 4),
            (UnitInfo.ARCHER, 4, 4),
            (UnitInfo.KNIGHT, 3, 3),
            (UnitInfo.SCOUT_CAVALRY, 2, 3),
            (UnitInfo.PIKEMAN, 2, 3),
        ]
        for unit, groups, size in troop_mix:
            _place_group(
                map_manager,
                district_points,
                MapLayerType.UNIT,
                unit,
                player_id,
                groups=_scaled_count(groups, density_scale),
                group_size=_scaled_count(size, density_scale),
                clumping=3,
            )

        decor_choices = [
            OtherInfo.FLAG_A,
            OtherInfo.FLAG_D,
            OtherInfo.FLAG_H,
            OtherInfo.TORCH_A,
            OtherInfo.TORCH_B,
            OtherInfo.RUBBLE_2_X_2,
            OtherInfo.RUBBLE_3_X_3,
            OtherInfo.ROCK_1,
        ]
        for decor_obj in decor_choices:
            _place_group(
                map_manager,
                district_points,
                MapLayerType.DECOR,
                decor_obj,
                PlayerId.GAIA,
                groups=_scaled_count(2, density_scale),
                group_size=_scaled_count(2, density_scale),
                clumping=3,
            )

        # Yard paths make this district visually coherent.
        path_targets = [
            (center[0] - int(ring_radius), center[1]),
            (center[0] + int(ring_radius), center[1]),
        ]
        for target in path_targets:
            map_manager.path_placer.create_path(
                PlacePathConfig(
                    point_collection=district_points.copy(),
                    map_layer_type=MapLayerType.TERRAIN,
                    obj_type=TerrainId.ROAD,
                    player_id=player_id,
                    key_points=[center, target],
                    num_divisions=[2],
                    random_shift_range=[1],
                )
            )

        return DistrictPlacementResult("military", center, _bounding_box(district_points))


class CityMarketDistrictTemplate:
    """Market district: commerce buildings, trade carts, and civilian decor."""

    @staticmethod
    def generate(
        map_manager: IMapManager,
        district_points: PointCollection,
        fallback_center: Point,
        city_radius: float,
        player_id: PlayerId,
        rng: random.Random,
        density_scale: float = 1.0,
    ) -> DistrictPlacementResult:
        center = _safe_average(district_points, fallback_center)
        if not district_points.get_point_list():
            return DistrictPlacementResult("market", center, None)

        _place_building(
            map_manager,
            district_points,
            center,
            BuildingInfo.MARKET,
            player_id,
            margin=1,
        )
        _place_building(
            map_manager,
            district_points,
            (center[0] + 7, center[1] - 2),
            BuildingInfo.TRADE_WORKSHOP,
            player_id,
        )
        _place_building(
            map_manager,
            district_points,
            (center[0] - 7, center[1] + 1),
            BuildingInfo.HOUSE,
            player_id,
        )

        # Ensure carts definitely exist.
        _place_unit(
            map_manager,
            district_points,
            (center[0] + 2, center[1] + 2),
            UnitInfo.TRADE_CART_FULL,
            player_id,
        )
        _place_unit(
            map_manager,
            district_points,
            (center[0] - 2, center[1] - 2),
            UnitInfo.TRADE_CART_EMPTY,
            player_id,
        )

        cart_units = [UnitInfo.CART, UnitInfo.OX_CART, UnitInfo.TRADE_CART_EMPTY]
        for unit in cart_units:
            _place_group(
                map_manager,
                district_points,
                MapLayerType.UNIT,
                unit,
                player_id,
                groups=_scaled_count(2, density_scale),
                group_size=_scaled_count(2, density_scale),
                clumping=5,
            )

        villager_units = [
            UnitInfo.VILLAGER_MALE,
            UnitInfo.VILLAGER_FEMALE,
            UnitInfo.VILLAGER_MALE_FORAGER,
            UnitInfo.VILLAGER_FEMALE_BUILDER,
        ]
        for unit in villager_units:
            _place_group(
                map_manager,
                district_points,
                MapLayerType.UNIT,
                unit,
                player_id,
                groups=_scaled_count(2, density_scale),
                group_size=_scaled_count(2, density_scale),
                clumping=4,
            )

        market_decor = [
            OtherInfo.BARRELS,
            OtherInfo.BROKEN_CART,
            OtherInfo.DISMANTLED_CART,
            OtherInfo.SIGN,
            OtherInfo.WELL,
            OtherInfo.FLOWERS_1,
            OtherInfo.FLOWERS_3,
        ]
        for obj in market_decor:
            _place_group(
                map_manager,
                district_points,
                MapLayerType.DECOR,
                obj,
                PlayerId.GAIA,
                groups=_scaled_count(2, density_scale),
                group_size=_scaled_count(2, density_scale),
                clumping=4,
            )

        for angle in [0, 120, 240]:
            target = (
                int(center[0] + city_radius * 0.13 * math.cos(math.radians(angle))),
                int(center[1] + city_radius * 0.13 * math.sin(math.radians(angle))),
            )
            map_manager.path_placer.create_path(
                PlacePathConfig(
                    point_collection=district_points.copy(),
                    map_layer_type=MapLayerType.TERRAIN,
                    obj_type=TerrainId.DIRT_1,
                    player_id=player_id,
                    key_points=[center, target],
                    num_divisions=[2],
                    random_shift_range=[2],
                )
            )

        return DistrictPlacementResult("market", center, _bounding_box(district_points))


class CityVillageDistrictTemplate:
    """Village district: homes, farms, villagers, and soft natural decor."""

    @staticmethod
    def generate(
        map_manager: IMapManager,
        district_points: PointCollection,
        fallback_center: Point,
        city_radius: float,
        player_id: PlayerId,
        rng: random.Random,
        density_scale: float = 1.0,
    ) -> DistrictPlacementResult:
        center = _safe_average(district_points, fallback_center)
        if not district_points.get_point_list():
            return DistrictPlacementResult("village", center, None)

        _place_building(
            map_manager,
            district_points,
            center,
            BuildingInfo.TOWN_CENTER,
            player_id,
            margin=1,
        )
        _place_building(
            map_manager,
            district_points,
            (center[0] + 6, center[1] + 4),
            BuildingInfo.MILL,
            player_id,
        )

        house_groups = max(
            8,
            min(28, _scaled_count(len(district_points.get_point_list()) // 140, density_scale)),
        )
        _place_group(
            map_manager,
            district_points,
            MapLayerType.UNIT,
            BuildingInfo.HOUSE,
            player_id,
            groups=house_groups,
            group_size=1,
            clumping=6,
        )

        farm_source = _subset_within_radius(district_points, (center[0] + 6, center[1] + 4), 12)
        _place_group(
            map_manager,
            farm_source,
            MapLayerType.UNIT,
            BuildingInfo.FARM,
            player_id,
            groups=_scaled_count(8, density_scale),
            group_size=1,
            clumping=4,
        )

        # Resource nodes for trigger-driven villager work loops.
        _place_group(
            map_manager,
            _subset_within_radius(district_points, (center[0] - 9, center[1] + 3), 6),
            MapLayerType.UNIT,
            OtherInfo.STONE_MINE,
            PlayerId.GAIA,
            groups=1,
            group_size=2,
            clumping=2,
        )
        _place_group(
            map_manager,
            _subset_within_radius(district_points, (center[0] + 9, center[1] - 3), 6),
            MapLayerType.UNIT,
            OtherInfo.GOLD_MINE,
            PlayerId.GAIA,
            groups=1,
            group_size=2,
            clumping=2,
        )
        _place_group(
            map_manager,
            _subset_within_radius(district_points, (center[0] - 5, center[1] - 6), 6),
            MapLayerType.UNIT,
            OtherInfo.FORAGE_BUSH,
            PlayerId.GAIA,
            groups=1,
            group_size=4,
            clumping=3,
        )

        # Guarantee at least one villager exists in the district.
        _place_unit(map_manager, district_points, (center[0] + 1, center[1]), UnitInfo.VILLAGER_MALE, player_id)

        villagers = [
            UnitInfo.VILLAGER_MALE_FARMER,
            UnitInfo.VILLAGER_FEMALE_FARMER,
            UnitInfo.VILLAGER_MALE_LUMBERJACK,
            UnitInfo.VILLAGER_FEMALE_FORAGER,
            UnitInfo.VILLAGER_MALE_BUILDER,
            UnitInfo.VILLAGER_FEMALE_SHEPHERD,
        ]
        for villager in villagers:
            _place_group(
                map_manager,
                district_points,
                MapLayerType.UNIT,
                villager,
                player_id,
                groups=_scaled_count(2, density_scale),
                group_size=_scaled_count(2, density_scale),
                clumping=5,
            )

        village_decor = [
            OtherInfo.TREE_OAK,
            OtherInfo.TREE_A,
            OtherInfo.TREE_B,
            OtherInfo.BUSH_A,
            OtherInfo.BUSH_C,
            OtherInfo.FLOWERS_2,
            OtherInfo.FLOWERS_4,
            OtherInfo.WELL,
        ]
        for obj in village_decor:
            layer = MapLayerType.UNIT if "TREE" in obj._name_ else MapLayerType.DECOR
            _place_group(
                map_manager,
                district_points,
                layer,
                obj,
                PlayerId.GAIA,
                groups=_scaled_count(2, density_scale),
                group_size=_scaled_count(3 if "TREE" in obj._name_ else 2, density_scale),
                clumping=5,
            )

        pond_points = _subset_within_radius(
            district_points,
            (center[0] - 8, center[1] + 10),
            radius=max(4.0, city_radius * 0.06),
        )
        _place_group(
            map_manager,
            pond_points,
            MapLayerType.TERRAIN,
            TerrainId.SHALLOWS,
            PlayerId.GAIA,
            groups=1,
            group_size=_scaled_count(24, density_scale, minimum=8),
            clumping=4,
        )

        return DistrictPlacementResult("village", center, _bounding_box(district_points))
