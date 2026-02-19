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
