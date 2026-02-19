"""
Tests for MapManager gate-placement methods:
  - place_gates_on_four_sides
  - place_gates_on_eight_sides

The map layer dictionary is keyed by ``MapObject`` with ``set[tuple[int,int]]``
values.  Tests verify that at least one real (non-empty, non-ghost) object is
placed for the owning player after each call.
"""

import os

import pytest
from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceGateOnFourSidesConfig,
    PlaceGateOnEightSidesConfig,
    VisualizeMapConfig,
)
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
    LINUX_PROJECT_UNIT_TEST_IMAGES_PATH,
)
from aoe2mapgenerator.utils.utils import combine_test_name_and_function_name

FILE_NAME = os.path.basename(__file__).replace(".py", "")


# ── Helpers ───────────────────────────────────────────────────────────────

def _make_map_with_points(n: int) -> MapManager:
    """Return a fresh n×n MapManager with all tiles registered."""
    mgr = MapManager(n)
    mgr.point_manager.add_point_collection("base_points")
    mgr.point_manager.get_point_collection("base_points").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )
    return mgr


def _count_owned_real_tiles(
    map_manager: MapManager,
    map_layer_type: MapLayerType,
    player_id: PlayerId,
) -> int:
    """Count tiles that hold a real (non-empty, non-ghost) object for player_id."""
    layer_dict = map_manager.get_dictionary(map_layer_type)
    total = 0
    for map_obj, coords in layer_dict.items():
        if not coords:
            continue
        if map_obj.obj_type == DEFAULT_EMPTY_VALUE:
            continue
        if map_obj.obj_type == GHOST_OBJECT_DISPLACEMENT_ID:
            continue
        if map_obj.player_id == player_id:
            total += len(coords)
    return total


# ── Four sides ─────────────────────────────────────────────────────────────

def test_place_gates_on_four_sides(should_visualize: bool) -> None:
    """At least one gate tile should be placed on four sides."""
    n = 50
    map_manager = _make_map_with_points(n)

    configuration = PlaceGateOnFourSidesConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        gate_type=GateType.FORTIFIED_GATE,
        player_id=PlayerId.ONE,
    )

    map_manager.place_gates_on_four_sides(configuration)

    placed = _count_owned_real_tiles(map_manager, MapLayerType.UNIT, PlayerId.ONE)

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

    assert placed > 0, "place_gates_on_four_sides should place at least one gate tile"


def test_place_gates_on_four_sides_gaia(should_visualize: bool) -> None:
    """GAIA city gates should also place without error."""
    n = 50
    map_manager = _make_map_with_points(n)

    configuration = PlaceGateOnFourSidesConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        gate_type=GateType.CITY_GATE,
        player_id=PlayerId.GAIA,
    )

    map_manager.place_gates_on_four_sides(configuration)

    # For GAIA, filter out DEFAULT_EMPTY_VALUE (which is also player GAIA/0)
    layer_dict = map_manager.get_dictionary(MapLayerType.UNIT)
    placed = sum(
        len(coords)
        for map_obj, coords in layer_dict.items()
        if coords
        and map_obj.obj_type != DEFAULT_EMPTY_VALUE
        and map_obj.obj_type != GHOST_OBJECT_DISPLACEMENT_ID
        and map_obj.player_id == PlayerId.GAIA
    )

    assert placed > 0, "GAIA city gate placement should place at least one tile"


# ── Eight sides ────────────────────────────────────────────────────────────

def test_place_gates_on_eight_sides(should_visualize: bool) -> None:
    """At least one gate tile should be placed on eight sides."""
    n = 50
    map_manager = _make_map_with_points(n)

    configuration = PlaceGateOnEightSidesConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        gate_type=GateType.FORTIFIED_GATE,
        player_id=PlayerId.TWO,
    )

    map_manager.place_gates_on_eight_sides(configuration)

    placed = _count_owned_real_tiles(map_manager, MapLayerType.UNIT, PlayerId.TWO)

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

    assert placed > 0, "place_gates_on_eight_sides should place at least one gate tile"


# ── No-crash on small region ───────────────────────────────────────────────

def test_gates_do_not_raise_on_small_region(should_visualize: bool) -> None:
    """Placing gates on a tiny 10x10 region should not raise."""
    n = 10
    map_manager = _make_map_with_points(n)

    configuration = PlaceGateOnFourSidesConfig(
        point_collection=map_manager.point_manager.get_point_collection("base_points"),
        map_layer_type=MapLayerType.UNIT,
        gate_type=GateType.FORTIFIED_GATE,
        player_id=PlayerId.ONE,
    )

    # Should not raise regardless of whether placement succeeds
    map_manager.place_gates_on_four_sides(configuration)
