"""Deterministic prefab definitions for CITY wards."""

from __future__ import annotations

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.templates.city_layout_plan import PrefabPlacement, PrefabSpec

Point = tuple[int, int]


def _pp(offset: Point, layer: MapLayerType, obj_type, player_id: PlayerId, margin: int = 0) -> PrefabPlacement:
    return PrefabPlacement(offset=offset, layer=layer, obj_type=obj_type, player_id=player_id, margin=margin)


def _terrain(offset: Point, terrain) -> PrefabPlacement:
    return _pp(offset, MapLayerType.TERRAIN, terrain, PlayerId.GAIA)


def _decor(offset: Point, decor) -> PrefabPlacement:
    return _pp(offset, MapLayerType.DECOR, decor, PlayerId.GAIA)


def _unit(offset: Point, obj, player_id: PlayerId = PlayerId.ONE, margin: int = 0) -> PrefabPlacement:
    return _pp(offset, MapLayerType.UNIT, obj, player_id, margin)


def _rect_mask(half_h: int, half_w: int) -> list[Point]:
    return [(dr, dc) for dr in range(-half_h, half_h + 1) for dc in range(-half_w, half_w + 1)]


def _diamond_mask(radius: int) -> list[Point]:
    return [(dr, dc) for dr in range(-radius, radius + 1) for dc in range(-radius, radius + 1) if abs(dr) + abs(dc) <= radius]


CITY_PREFABS: dict[str, PrefabSpec] = {
    "GatehouseCardinalPrefab": PrefabSpec(
        name="GatehouseCardinalPrefab",
        footprint_mask=_rect_mask(4, 5),
        reserved_mask=_rect_mask(5, 6),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.GUARD_TOWER, margin=1),
            _unit((0, 4), BuildingInfo.GUARD_TOWER, margin=1),
            _unit((2, 2), UnitInfo.SPEARMAN),
            _unit((2, 3), UnitInfo.ARCHER),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.ROAD) for dr in range(1, 5) for dc in range(0, 5)],
        decor_tiles=[
            _decor((-2, 1), OtherInfo.TORCH_A),
            _decor((-2, 3), OtherInfo.TORCH_B),
            _decor((1, -1), OtherInfo.FLAG_A),
            _decor((1, 5), OtherInfo.FLAG_D),
        ],
        allowed_transforms=("identity", "rot90", "rot180", "rot270"),
    ),
    "GatehouseDiagonalPrefab": PrefabSpec(
        name="GatehouseDiagonalPrefab",
        footprint_mask=_diamond_mask(4),
        reserved_mask=_diamond_mask(5),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.GUARD_TOWER, margin=1),
            _unit((2, 2), BuildingInfo.GUARD_TOWER, margin=1),
            _unit((1, 0), UnitInfo.SPEARMAN),
            _unit((2, 1), UnitInfo.ARCHER),
        ],
        terrain_tiles=[_terrain(offset, TerrainId.ROAD) for offset in _diamond_mask(3)],
        decor_tiles=[
            _decor((-1, 2), OtherInfo.TORCH_A),
            _decor((2, -1), OtherInfo.TORCH_B),
            _decor((0, 3), OtherInfo.FLAG_H),
        ],
        allowed_transforms=("identity", "rot90", "rot180", "rot270"),
    ),
    "MilitaryYardPrefab_A": PrefabSpec(
        name="MilitaryYardPrefab_A",
        footprint_mask=_rect_mask(6, 6),
        reserved_mask=_rect_mask(7, 7),
        unit_tiles=[
            _unit((-2, -2), BuildingInfo.BARRACKS, margin=1),
            _unit((2, 2), BuildingInfo.ARCHERY_RANGE, margin=1),
            _unit((0, -5), UnitInfo.MAN_AT_ARMS),
            _unit((1, -5), UnitInfo.SPEARMAN),
            _unit((4, 0), UnitInfo.ARCHER),
            _unit((4, 1), UnitInfo.ARCHER),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-4, 5) for dc in range(-4, 5)],
        decor_tiles=[_decor((0, 5), OtherInfo.FLAG_A), _decor((-5, 0), OtherInfo.TORCH_A), _decor((5, 0), OtherInfo.RUBBLE_2_X_2)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "MilitaryYardPrefab_B": PrefabSpec(
        name="MilitaryYardPrefab_B",
        footprint_mask=_rect_mask(6, 6),
        reserved_mask=_rect_mask(7, 7),
        unit_tiles=[
            _unit((-2, -2), BuildingInfo.STABLE, margin=1),
            _unit((2, 2), BuildingInfo.BLACKSMITH, margin=1),
            _unit((0, -4), UnitInfo.KNIGHT),
            _unit((1, -4), UnitInfo.SCOUT_CAVALRY),
            _unit((4, 0), UnitInfo.PIKEMAN),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-4, 5) for dc in range(-4, 5)],
        decor_tiles=[_decor((-5, -1), OtherInfo.FLAG_D), _decor((5, 1), OtherInfo.TORCH_B), _decor((0, 5), OtherInfo.ROCK_1)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "SiegeYardPrefab": PrefabSpec(
        name="SiegeYardPrefab",
        footprint_mask=_rect_mask(5, 6),
        reserved_mask=_rect_mask(6, 7),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.SIEGE_WORKSHOP, margin=1),
            _unit((4, -2), UnitInfo.SPEARMAN),
            _unit((4, -1), UnitInfo.SPEARMAN),
            _unit((4, 1), UnitInfo.KNIGHT),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-3, 5) for dc in range(-5, 6)],
        decor_tiles=[_decor((-4, -4), OtherInfo.BARRELS), _decor((-4, 4), OtherInfo.BROKEN_CART), _decor((3, 4), OtherInfo.DISMANTLED_CART)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270"),
    ),
    "MarketPlazaCorePrefab": PrefabSpec(
        name="MarketPlazaCorePrefab",
        footprint_mask=_rect_mask(6, 8),
        reserved_mask=_rect_mask(7, 9),
        unit_tiles=[
            _unit((0, -3), BuildingInfo.MARKET, margin=1),
            _unit((0, 4), BuildingInfo.TRADE_WORKSHOP, margin=1),
            _unit((4, -5), UnitInfo.TRADE_CART_FULL),
            _unit((4, -4), UnitInfo.TRADE_CART_EMPTY),
            _unit((4, 5), UnitInfo.VILLAGER_FEMALE),
            _unit((4, 4), UnitInfo.VILLAGER_MALE),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.ROAD) for dr in range(-5, 6) for dc in range(-7, 8)],
        decor_tiles=[
            _decor((0, 0), OtherInfo.WELL),
            _decor((-4, 0), OtherInfo.SIGN),
            _decor((2, 0), OtherInfo.BARRELS),
            _decor((2, 2), OtherInfo.FLOWERS_1),
        ],
        allowed_transforms=("identity", "rot90", "rot180", "rot270"),
    ),
    "MarketLanePrefab_A": PrefabSpec(
        name="MarketLanePrefab_A",
        footprint_mask=_rect_mask(3, 5),
        reserved_mask=_rect_mask(4, 6),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.HOUSE, margin=1),
            _unit((2, -4), UnitInfo.VILLAGER_MALE),
            _unit((2, 4), UnitInfo.CART),
        ],
        terrain_tiles=[_terrain((0, dc), TerrainId.DIRT_1) for dc in range(-5, 6)],
        decor_tiles=[_decor((-2, -3), OtherInfo.BARRELS), _decor((-2, 3), OtherInfo.FLOWERS_3)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "MarketLanePrefab_B": PrefabSpec(
        name="MarketLanePrefab_B",
        footprint_mask=_rect_mask(3, 5),
        reserved_mask=_rect_mask(4, 6),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.HOUSE, margin=1),
            _unit((1, -4), UnitInfo.OX_CART),
            _unit((2, 4), UnitInfo.VILLAGER_FEMALE),
        ],
        terrain_tiles=[_terrain((0, dc), TerrainId.DIRT_1) for dc in range(-5, 6)],
        decor_tiles=[_decor((-2, -2), OtherInfo.SIGN), _decor((-2, 2), OtherInfo.FLOWERS_1)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "TownCommonsPrefab": PrefabSpec(
        name="TownCommonsPrefab",
        footprint_mask=_rect_mask(8, 8),
        reserved_mask=_rect_mask(9, 9),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.TOWN_CENTER, margin=1),
            _unit((5, 4), BuildingInfo.MILL, margin=1),
            _unit((-5, 0), UnitInfo.VILLAGER_MALE),
            _unit((-4, 1), UnitInfo.VILLAGER_FEMALE),
            _unit((-4, -1), UnitInfo.VILLAGER_MALE_FARMER),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.ROAD) for dr in range(-7, 8) for dc in range(-7, 8) if abs(dr) + abs(dc) <= 11],
        decor_tiles=[_decor((0, 6), OtherInfo.WELL), _decor((6, -1), OtherInfo.FLOWERS_2), _decor((-6, 1), OtherInfo.TREE_OAK)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270"),
    ),
    "FarmsteadBlockPrefab": PrefabSpec(
        name="FarmsteadBlockPrefab",
        footprint_mask=_rect_mask(6, 7),
        reserved_mask=_rect_mask(7, 8),
        unit_tiles=[
            _unit((0, 0), BuildingInfo.FARM),
            _unit((0, 4), BuildingInfo.FARM),
            _unit((3, 2), BuildingInfo.FARM),
            _unit((-4, -3), UnitInfo.VILLAGER_MALE_FARMER),
            _unit((-4, -2), UnitInfo.VILLAGER_FEMALE_FARMER),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-5, 6) for dc in range(-6, 7) if (dr % 3 == 0 or dc % 4 == 0)],
        decor_tiles=[_decor((4, -5), OtherInfo.BUSH_A), _decor((4, 5), OtherInfo.TREE_A)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "ResidentialCourtyardPrefab_A": PrefabSpec(
        name="ResidentialCourtyardPrefab_A",
        footprint_mask=_rect_mask(6, 6),
        reserved_mask=_rect_mask(7, 7),
        unit_tiles=[
            _unit((-3, -3), BuildingInfo.HOUSE, margin=1),
            _unit((-3, 3), BuildingInfo.HOUSE, margin=1),
            _unit((3, -3), BuildingInfo.HOUSE, margin=1),
            _unit((2, 2), UnitInfo.VILLAGER_FEMALE),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-2, 3) for dc in range(-2, 3)],
        decor_tiles=[_decor((0, 0), OtherInfo.WELL), _decor((1, 1), OtherInfo.FLOWERS_4), _decor((-1, -1), OtherInfo.BUSH_C), _decor((0, 3), OtherInfo.TREE_B)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "ResidentialCourtyardPrefab_B": PrefabSpec(
        name="ResidentialCourtyardPrefab_B",
        footprint_mask=_rect_mask(6, 6),
        reserved_mask=_rect_mask(7, 7),
        unit_tiles=[
            _unit((-3, 0), BuildingInfo.HOUSE, margin=1),
            _unit((3, 0), BuildingInfo.HOUSE, margin=1),
            _unit((0, -3), BuildingInfo.HOUSE, margin=1),
            _unit((0, 3), BuildingInfo.HOUSE, margin=1),
            _unit((2, 2), UnitInfo.VILLAGER_MALE),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-5, 6) for dc in range(-5, 6) if dr == 0 or dc == 0],
        decor_tiles=[_decor((0, 0), OtherInfo.WELL), _decor((2, -1), OtherInfo.FLOWERS_2), _decor((-2, 1), OtherInfo.TREE_OAK)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "ResidentialCourtyardPrefab_C": PrefabSpec(
        name="ResidentialCourtyardPrefab_C",
        footprint_mask=_rect_mask(5, 6),
        reserved_mask=_rect_mask(6, 7),
        unit_tiles=[
            _unit((-2, -3), BuildingInfo.HOUSE, margin=1),
            _unit((-2, 3), BuildingInfo.HOUSE, margin=1),
            _unit((2, 0), BuildingInfo.HOUSE, margin=1),
            _unit((4, 2), UnitInfo.VILLAGER_FEMALE),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.DIRT_1) for dr in range(-1, 4) for dc in range(-2, 3)],
        decor_tiles=[_decor((0, 0), OtherInfo.WELL), _decor((1, -2), OtherInfo.BUSH_A), _decor((1, 2), OtherInfo.FLOWERS_2)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "NobleCourtyardPrefab": PrefabSpec(
        name="NobleCourtyardPrefab",
        footprint_mask=_rect_mask(7, 8),
        reserved_mask=_rect_mask(8, 9),
        unit_tiles=[
            _unit((-3, -4), BuildingInfo.HOUSE, margin=1),
            _unit((-3, 4), BuildingInfo.HOUSE, margin=1),
            _unit((3, 0), BuildingInfo.HOUSE, margin=1),
            _unit((0, 0), UnitInfo.VILLAGER_FEMALE_BUILDER),
            _unit((1, 1), UnitInfo.VILLAGER_MALE_BUILDER),
        ],
        terrain_tiles=[_terrain((dr, dc), TerrainId.ROAD) for dr in range(-6, 7) for dc in range(-7, 8) if abs(dr) <= 1 or abs(dc) <= 1],
        decor_tiles=[_decor((0, -2), OtherInfo.FLOWERS_1), _decor((0, 2), OtherInfo.FLOWERS_3), _decor((-5, 0), OtherInfo.FLAG_H), _decor((5, 0), OtherInfo.TORCH_A)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270"),
    ),
    "GardenPocketPrefab_A": PrefabSpec(
        name="GardenPocketPrefab_A",
        footprint_mask=_rect_mask(4, 4),
        reserved_mask=_rect_mask(4, 4),
        unit_tiles=[
            _unit((-2, -1), OtherInfo.TREE_OAK, PlayerId.GAIA),
            _unit((1, 2), OtherInfo.TREE_A, PlayerId.GAIA),
            _unit((2, -2), OtherInfo.TREE_B, PlayerId.GAIA),
        ],
        terrain_tiles=[],
        decor_tiles=[_decor((0, 0), OtherInfo.FLOWERS_1), _decor((0, 1), OtherInfo.BUSH_A), _decor((-1, 1), OtherInfo.ROCK_1)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "GardenPocketPrefab_B": PrefabSpec(
        name="GardenPocketPrefab_B",
        footprint_mask=_rect_mask(4, 4),
        reserved_mask=_rect_mask(4, 4),
        unit_tiles=[
            _unit((-2, 0), OtherInfo.TREE_OAK, PlayerId.GAIA),
            _unit((0, 2), OtherInfo.TREE_B, PlayerId.GAIA),
        ],
        terrain_tiles=[],
        decor_tiles=[_decor((0, 0), OtherInfo.FLOWERS_2), _decor((1, -1), OtherInfo.BUSH_B), _decor((-1, -1), OtherInfo.ROCK_2)],
        allowed_transforms=("identity", "rot90", "rot180", "rot270", "mirror"),
    ),
    "StreetTreeStripPrefab": PrefabSpec(
        name="StreetTreeStripPrefab",
        footprint_mask=[(0, dc) for dc in range(-4, 5)],
        reserved_mask=[(0, dc) for dc in range(-5, 6)],
        unit_tiles=[
            _unit((0, -3), OtherInfo.TREE_OAK, PlayerId.GAIA),
            _unit((0, 0), OtherInfo.TREE_A, PlayerId.GAIA),
            _unit((0, 3), OtherInfo.TREE_B, PlayerId.GAIA),
        ],
        terrain_tiles=[],
        decor_tiles=[_decor((0, -2), OtherInfo.FLOWERS_1), _decor((0, 1), OtherInfo.FLOWERS_2)],
        allowed_transforms=("identity", "rot90"),
    ),
}


def get_city_prefab(name: str) -> PrefabSpec:
    return CITY_PREFABS[name]

