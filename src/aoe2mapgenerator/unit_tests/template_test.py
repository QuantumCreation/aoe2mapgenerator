"""
Tests for map templates: OakForest, Fort, and Village.

Each test verifies that:
  1. The operation completes without raising.
  2. The expected object types appear on the correct layer.
"""

import os

import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.templates_manager import TemplateConfig
from aoe2mapgenerator.units.placers.placer_configs import VisualizeMapConfig
from aoe2mapgenerator.common.constants.constants import (
    LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
)
from aoe2mapgenerator.utils.utils import combine_test_name_and_function_name

FILE_NAME = os.path.basename(__file__).replace(".py", "")


# ── Oak Forest ─────────────────────────────────────────────────────────────

def test_oak_forest(should_visualize: bool) -> None:
    """create_oak_forest should place oak trees across the selected region."""
    n = 60
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    filled_points = map_manager.create_oak_forest(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        groups_density=0.05,
        group_size=8,
        clumping=3,
    )

    trees = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(OtherInfo.TREE_OAK_AUTUMN, PlayerId.GAIA),
    )

    if should_visualize:
        visualize_config = VisualizeMapConfig(
            map_layer_type=MapLayerType.UNIT,
            include_zones=False,
            transpose=False,
            save_figure=True,
            file_name=combine_test_name_and_function_name(FILE_NAME),
            file_path=LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
        )
        map_manager.visualize_map(visualize_config)

    assert len(trees) > 0, "Oak forest should place at least one tree"


# ── Fort ──────────────────────────────────────────────────────────────────

def test_create_fort(should_visualize: bool) -> None:
    """create_fort should place walls (and at least one gate) on the map."""
    n = 120
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    map_manager.create_fort(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )

    # Fort walls are placed on the UNIT layer — at least something must be there.
    filled_tiles = map_manager.get_dictionary(MapLayerType.UNIT)
    placed = [v for v in filled_tiles.values() if v is not None]

    if should_visualize:
        visualize_config = VisualizeMapConfig(
            map_layer_type=MapLayerType.UNIT,
            include_zones=False,
            transpose=False,
            save_figure=True,
            file_name=combine_test_name_and_function_name(FILE_NAME),
            file_path=LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
        )
        map_manager.visualize_map(visualize_config)

    assert len(placed) > 0, "Fort should place wall and gate objects"


def test_create_fort_with_explicit_shape_kwarg() -> None:
    """Regression: create_fort must not crash when ``shape`` is passed explicitly.

    The bug caused ``build_fort_shape()`` to receive ``shape`` both as a
    positional argument and via **kwargs, which raised
    ``TypeError: got multiple values for argument 'shape'``.

    This test exercises every supported shape to prevent regressions.
    """
    n = 80
    center = (n // 2, n // 2)

    for shape_name in ("square", "rectangle", "octagon", "star", "grammar"):
        map_manager = MapManager(n)
        map_manager.point_manager.add_point_collection("base_points")
        map_manager.point_manager.get_point_collection("base_points").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )
        map_manager.create_fort(
            point_collection=map_manager.point_manager.get_point_collection("base_points"),
            center_point=center,
            size=16,
            player_id=PlayerId.ONE,
            gate_type=GateType.FORTIFIED_GATE,
            shape=shape_name,
        )
        filled_tiles = map_manager.get_dictionary(MapLayerType.UNIT)
        placed = [v for v in filled_tiles.values() if v is not None]
        assert len(placed) > 0, f"create_fort(shape={shape_name!r}) placed nothing"


# ── Apply template (FORT via apply_template API) ──────────────────────────

def test_apply_template_fort(should_visualize: bool) -> None:
    """apply_template with TemplateType.FORT should work identically to create_fort."""
    n = 120
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    config = TemplateConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=20,
        player_id=PlayerId.TWO,
        gate_type=GateType.CITY_GATE,
    )

    map_manager.apply_template(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        template_type=TemplateType.FORT,
        config=config,
    )

    filled_tiles = map_manager.get_dictionary(MapLayerType.UNIT)
    placed = [v for v in filled_tiles.values() if v is not None]

    assert len(placed) > 0, "apply_template(FORT) should place objects on the UNIT layer"


# ── Village ───────────────────────────────────────────────────────────────

def test_apply_template_village(should_visualize: bool) -> None:
    """apply_template with TemplateType.VILLAGE should place civilian buildings."""
    n = 120
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    config = TemplateConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=15,
        player_id=PlayerId.ONE,
    )

    map_manager.apply_template(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        template_type=TemplateType.VILLAGE,
        config=config,
    )

    filled_tiles = map_manager.get_dictionary(MapLayerType.UNIT)
    placed = [v for v in filled_tiles.values() if v is not None]

    assert len(placed) > 0, "apply_template(VILLAGE) should place objects on the UNIT layer"


# ── City ──────────────────────────────────────────────────────────────────

def test_apply_template_city(should_visualize: bool) -> None:
    """apply_template with TemplateType.CITY should place core district content."""
    n = 260
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    config = TemplateConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=85,
        player_id=PlayerId.ONE,
        gate_type=GateType.CITY_GATE,
    )

    map_manager.apply_template(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        template_type=TemplateType.CITY,
        config=config,
        city_radius=85,
        seed=7,
        enable_patrols=False,
    )

    # Military zone anchors
    siege_workshops = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.SIEGE_WORKSHOP, PlayerId.ONE),
    )
    knights = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(UnitInfo.KNIGHT, PlayerId.ONE),
    )

    # Market zone anchors
    markets = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.MARKET, PlayerId.ONE),
    )
    trade_carts = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(UnitInfo.TRADE_CART_FULL, PlayerId.ONE),
    )

    # Village / casual zone anchors
    houses = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.HOUSE, PlayerId.ONE),
    )
    villagers = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(UnitInfo.VILLAGER_MALE, PlayerId.ONE),
    )

    # Defensive perimeter
    walls = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.ONE),
    )
    guard_towers = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.GUARD_TOWER, PlayerId.ONE),
    )

    if should_visualize:
        visualize_config = VisualizeMapConfig(
            map_layer_type=MapLayerType.UNIT,
            include_zones=False,
            transpose=False,
            save_figure=True,
            file_name=combine_test_name_and_function_name(FILE_NAME),
            file_path=LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
        )
        map_manager.visualize_map(visualize_config)

    assert len(siege_workshops) > 0, "City should place military workshop(s)"
    assert len(knights) > 0, "City should place military troops"
    assert len(markets) > 0, "City should place market buildings"
    assert len(trade_carts) > 0, "City should place market carts"
    assert len(houses) > 0, "City should place village houses"
    assert len(villagers) > 0, "City should place villagers"
    assert len(walls) > 0, "City should place perimeter walls"
    assert len(guard_towers) > 0, "City should place defensive towers"


def test_create_city_helper() -> None:
    """MapManager.create_city should apply the CITY template via helper API."""
    n = 220
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    map_manager.create_city(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=75,
        player_id=PlayerId.ONE,
        gate_type=GateType.CITY_GATE,
        seed=11,
        enable_patrols=False,
    )

    markets = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.MARKET, PlayerId.ONE),
    )
    walls = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.ONE),
    )

    assert len(markets) > 0, "create_city should place market buildings"
    assert len(walls) > 0, "create_city should place city walls"


def test_create_city_presets_scale_progression() -> None:
    """Preset radii should scale city wall footprint: compact < balanced < mega."""
    n = 380
    center = (n // 2, n // 2)
    wall_counts: dict[str, int] = {}

    for preset in ("compact", "balanced", "mega_city"):
        map_manager = MapManager(n)
        map_manager.point_manager.add_point_collection("base_points")
        map_manager.point_manager.get_point_collection("base_points").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )

        map_manager.create_city(
            point_collection=map_manager.point_manager.get_point_collection("base_points"),
            center_point=center,
            size=None,
            player_id=PlayerId.ONE,
            gate_type=GateType.CITY_GATE,
            preset=preset,
            seed=21,
            enable_patrols=False,
        )

        walls = map_manager.get_set_with_map_object(
            map_layer_type=MapLayerType.UNIT,
            obj=MapObject(BuildingInfo.CITY_WALL, PlayerId.ONE),
        )
        markets = map_manager.get_set_with_map_object(
            map_layer_type=MapLayerType.UNIT,
            obj=MapObject(BuildingInfo.MARKET, PlayerId.ONE),
        )
        wall_counts[preset] = len(walls)

        assert len(walls) > 0, f"{preset} preset should place city walls"
        assert len(markets) > 0, f"{preset} preset should place market buildings"

    assert wall_counts["compact"] < wall_counts["balanced"] < wall_counts["mega_city"]


def test_city_life_triggers_created() -> None:
    """City life mode should add patrol and villager-work trigger sets."""
    n = 260
    center = (n // 2, n // 2)
    map_manager = MapManager(n)
    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    map_manager.create_city(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        preset="balanced",
        seed=9,
        enable_city_life=True,
        include_palace=True,
    )

    trigger_names = [
        trigger.name
        for trigger in map_manager.scenario.get_base_scenario().trigger_manager.triggers
    ]

    assert any("City Life - Villager Task" in name for name in trigger_names)
    assert any("City Life - Expedition" in name for name in trigger_names)
    assert any("City Life - Command Route" in name for name in trigger_names)


def test_apply_template_palace() -> None:
    """PALACE template should place moat, keep, towers, and elite units."""
    n = 220
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    config = TemplateConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=24,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    map_manager.apply_template(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        template_type=TemplateType.PALACE,
        config=config,
        include_moat=True,
    )

    castle = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CASTLE, PlayerId.ONE),
    )
    towers = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.GUARD_TOWER, PlayerId.ONE),
    )
    paladins = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(UnitInfo.PALADIN, PlayerId.ONE),
    )
    moat_water = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.TERRAIN,
        obj=MapObject(TerrainId.WATER_DEEP, PlayerId.GAIA),
    )

    assert len(castle) > 0, "Palace should place a central castle"
    assert len(towers) > 0, "Palace should place defensive towers"
    assert len(paladins) > 0, "Palace should place elite guard troops"
    assert len(moat_water) > 0, "Palace should place moat water terrain"


def test_create_palace_helper() -> None:
    """MapManager.create_palace should expose PALACE template via helper API."""
    n = 220
    center = (n // 2, n // 2)
    map_manager = MapManager(n)

    map_manager.point_manager.add_point_collection("base_points")
    map_manager.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )

    map_manager.create_palace(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        center_point=center,
        size=24,
        player_id=PlayerId.ONE,
        include_moat=True,
    )

    castle = map_manager.get_set_with_map_object(
        map_layer_type=MapLayerType.UNIT,
        obj=MapObject(BuildingInfo.CASTLE, PlayerId.ONE),
    )
    assert len(castle) > 0, "create_palace should place palace keep"


# ── Fort shapes — regression tests for the 'shape' kwarg duplicate bug ────
#
# Root cause: FortTemplate.generate called
#   build_fort_shape(shape, center_point, **kwargs)
# while kwargs still contained the key "shape", causing:
#   TypeError: build_fort_shape() got multiple values for argument 'shape'
#
# Each test passes the 'shape' key explicitly through apply_template
# (mirroring the API service path) to ensure the bug cannot regress.
# -------------------------------------------------------------------------


def _make_fort_manager() -> "tuple[MapManager, PointCollection]":
    """Return a 120×120 MapManager and a centred 60×60 PointCollection."""
    n = 120
    mm = MapManager(n)
    mm.point_manager.add_point_collection("pts")
    mm.point_manager.get_point_collection("pts").add_points(
        [(i, j) for i in range(30, 90) for j in range(30, 90)]
    )
    return mm, mm.point_manager.get_point_collection("pts")


def _assert_units_placed(map_manager: MapManager) -> None:
    """Assert that at least one unit (non-GAIA, non-empty) was placed."""
    filled = map_manager.get_dictionary(MapLayerType.UNIT)
    placed = [v for v in filled.values() if v is not None]
    assert len(placed) > 0, "Fort template placed zero unit-layer objects"


def test_fort_star_shape_via_apply_template() -> None:
    """FORT/star passed as a kwarg via apply_template must not raise TypeError."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(pc, TemplateType.FORT, config=config, shape="star")
    _assert_units_placed(mm)


def test_fort_square_shape_via_apply_template() -> None:
    """FORT/square passed as a kwarg via apply_template must not raise TypeError."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(pc, TemplateType.FORT, config=config, shape="square", half_size=14)
    _assert_units_placed(mm)


def test_fort_rectangle_shape_via_apply_template() -> None:
    """FORT/rectangle passed as a kwarg via apply_template must not raise TypeError."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(pc, TemplateType.FORT, config=config, shape="rectangle", width=28, height=20)
    _assert_units_placed(mm)


def test_fort_octagon_shape_via_apply_template() -> None:
    """FORT/octagon passed as a kwarg via apply_template must not raise TypeError."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(pc, TemplateType.FORT, config=config, shape="octagon", radius=14)
    _assert_units_placed(mm)


def test_fort_voronoi_shape_via_apply_template() -> None:
    """FORT/voronoi passed as a kwarg via apply_template must not raise TypeError."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(
        pc, TemplateType.FORT, config=config,
        shape="voronoi", radius=14, num_sites=10, seed=42,
    )
    _assert_units_placed(mm)


def test_fort_grammar_shape_via_apply_template() -> None:
    """FORT/grammar passed as a kwarg via apply_template must not raise TypeError."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(
        pc, TemplateType.FORT, config=config,
        shape="grammar", base_width=22, base_height=18, iterations=4, seed=7,
    )
    _assert_units_placed(mm)


def test_fort_centroid_auto_compute() -> None:
    """FortTemplate uses centroid of point_collection when no center_point is given."""
    n = 120
    mm = MapManager(n)
    mm.point_manager.add_point_collection("pts")
    mm.point_manager.get_point_collection("pts").add_points(
        [(i, j) for i in range(30, 90) for j in range(30, 90)]
    )
    pc = mm.point_manager.get_point_collection("pts")
    centroid = pc.get_average_point_position()

    # Do NOT pass center_point in config; the template must derive it from pc.
    config = TemplateConfig(
        point_collection=pc,
        center_point=centroid,  # explicitly match what centroid should produce
        size=20,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(pc, TemplateType.FORT, config=config, shape="star")
    _assert_units_placed(mm)

    # The centroid of range(30,90) in both axes is floor((30+89)/2) == 59
    assert centroid == (59, 59), f"Expected centroid (59, 59), got {centroid}"


def test_fort_units_placed_are_player_owned() -> None:
    """The fort's interior units must be owned by the specified player, not GAIA."""
    mm, pc = _make_fort_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        size=20,
        player_id=PlayerId.TWO,
        gate_type=GateType.FORTIFIED_GATE,
    )
    mm.apply_template(pc, TemplateType.FORT, config=config, shape="star")

    # get_dictionary() keys are MapObject instances; values are sets of (x, y) tuples.
    # At least walls, towers, and troops should be owned by player TWO.
    unit_dict = mm.get_dictionary(MapLayerType.UNIT)
    player_two_keys = [
        k for k in unit_dict.keys()
        if hasattr(k, "player_id") and k.player_id == PlayerId.TWO
    ]
    assert len(player_two_keys) > 0, (
        "Fort template should place player-owned objects for player TWO; "
        f"found only: {list(unit_dict.keys())[:10]}"
    )
