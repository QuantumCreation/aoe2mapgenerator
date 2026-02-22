"""Unit tests for nature area templates.

Each test verifies:
  1. The operation completes without raising.
  2. Expected terrain or object types appear on the correct map layer.

Templates tested:
  - SnowForestTemplate  (SNOW_FOREST)
  - PondTemplate        (POND)
  - RiverSegmentTemplate (RIVER_SEGMENT)
  - PineForestTemplate  (PINE_FOREST)
  - WinterLandscapeTemplate (WINTER_LANDSCAPE)
  - DesertTemplate      (DESERT)
  - DesertOasTemplate   (DESERT_OASIS)
  - SavannahTemplate    (SAVANNAH)
  - RainforestTemplate  (RAINFOREST)
  - MediterraneanTemplate (MEDITERRANEAN)

MapManager convenience helpers tested:
  create_snow_forest, create_pond, create_river_segment, create_pine_forest,
  create_winter_landscape, create_desert, create_desert_oasis, create_savannah,
  create_rainforest, create_mediterranean.
"""

import os
from typing import Tuple

import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.templates_manager import TemplateConfig
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_manager(n: int = 80) -> "tuple[MapManager, PointCollection]":
    """Return a fresh *n*×*n* MapManager with a full-coverage PointCollection."""
    mm = MapManager(n)
    mm.point_manager.add_point_collection("pts")
    mm.point_manager.get_point_collection("pts").add_points(
        [(i, j) for i in range(n) for j in range(n)]
    )
    return mm, mm.point_manager.get_point_collection("pts")


def _make_manager_region(
    n: int = 80,
    r0: int = 10,
    r1: int = 70,
) -> "tuple[MapManager, PointCollection]":
    """Return a MapManager whose PointCollection covers a sub-region [r0, r1)."""
    mm = MapManager(n)
    mm.point_manager.add_point_collection("pts")
    mm.point_manager.get_point_collection("pts").add_points(
        [(i, j) for i in range(r0, r1) for j in range(r0, r1)]
    )
    return mm, mm.point_manager.get_point_collection("pts")


def _any_terrain_placed(map_manager: MapManager) -> bool:
    """Return True if any terrain tile was set on the TERRAIN layer."""
    terrain = map_manager.get_dictionary(MapLayerType.TERRAIN)
    return any(v is not None for v in terrain.values())


def _any_unit_placed(map_manager: MapManager) -> bool:
    """Return True if any object was placed on the UNIT layer."""
    units = map_manager.get_dictionary(MapLayerType.UNIT)
    return any(v is not None for v in units.values())


def _specific_terrain_placed(map_manager: MapManager, terrain: TerrainId) -> bool:
    """Return True if *terrain* appears on the TERRAIN layer."""
    obj = MapObject(terrain, PlayerId.GAIA)
    tiles = map_manager.get_set_with_map_object(MapLayerType.TERRAIN, obj)
    return len(tiles) > 0


def _specific_unit_placed(
    map_manager: MapManager,
    unit: object,
    player: PlayerId = PlayerId.GAIA,
) -> bool:
    """Return True if *unit* (owned by *player*) appears on the UNIT layer."""
    obj = MapObject(unit, player)
    tiles = map_manager.get_set_with_map_object(MapLayerType.UNIT, obj)
    return len(tiles) > 0


# ---------------------------------------------------------------------------
# Snow Forest
# ---------------------------------------------------------------------------

def test_snow_forest_places_snow_terrain() -> None:
    """SnowForestTemplate should paint SNOW terrain on the selected region."""
    mm, pc = _make_manager()
    mm.create_snow_forest(pc, groups_density=0.05, group_size=8, clumping=3)
    assert _specific_terrain_placed(mm, TerrainId.SNOW), (
        "SNOW_FOREST should place SNOW terrain"
    )


def test_snow_forest_places_snow_pine_trees() -> None:
    """SnowForestTemplate should place TREE_SNOW_PINE objects."""
    mm, pc = _make_manager()
    mm.create_snow_forest(pc, groups_density=0.05, group_size=8, clumping=3)
    assert _specific_unit_placed(mm, OtherInfo.TREE_SNOW_PINE), (
        "SNOW_FOREST should place TREE_SNOW_PINE objects"
    )


def test_snow_forest_places_arctic_animals() -> None:
    """SnowForestTemplate should include wolves or snow leopards."""
    mm, pc = _make_manager()
    mm.create_snow_forest(pc, groups_density=0.05, group_size=8, clumping=3)
    has_wolf = _specific_unit_placed(mm, UnitInfo.WOLF)
    has_leopard = _specific_unit_placed(mm, UnitInfo.SNOW_LEOPARD)
    has_bear = _specific_unit_placed(mm, UnitInfo.BEAR)
    assert has_wolf or has_leopard or has_bear, (
        "SNOW_FOREST should place at least one arctic animal"
    )


# ---------------------------------------------------------------------------
# Pond
# ---------------------------------------------------------------------------

def test_pond_places_shallows_terrain() -> None:
    """PondTemplate should place SHALLOWS terrain at the pond centre."""
    mm, pc = _make_manager()
    center = (40, 40)
    mm.create_pond(pc, center_point=center, size=8)
    assert _specific_terrain_placed(mm, TerrainId.SHALLOWS), (
        "POND should place SHALLOWS terrain"
    )


def test_pond_places_fish() -> None:
    """PondTemplate should place at least one fish species in the pond."""
    mm, pc = _make_manager()
    mm.create_pond(pc, center_point=(40, 40), size=8)
    fish_placed = any(
        _specific_unit_placed(mm, fish)
        for fish in (
            OtherInfo.FISH_PERCH,
            OtherInfo.FISH_SALMON,
            OtherInfo.SHORE_FISH,
            OtherInfo.FISH_DORADO,
            OtherInfo.BOX_TURTLES,
        )
    )
    assert fish_placed, "POND should place at least one fish / aquatic species"


def test_pond_no_crash_small_region() -> None:
    """PondTemplate should not crash when the pond fits exactly in the region."""
    mm, pc = _make_manager_region(n=40, r0=15, r1=25)
    mm.create_pond(pc, center_point=(20, 20), size=4)
    # No crash — terrain or unit placement is best-effort
    assert True


# ---------------------------------------------------------------------------
# River segment
# ---------------------------------------------------------------------------

def test_river_segment_places_water_terrain() -> None:
    """RiverSegmentTemplate should fill the region with WATER_SHALLOW terrain."""
    mm, pc = _make_manager()
    mm.create_river_segment(pc)
    assert _specific_terrain_placed(mm, TerrainId.WATER_SHALLOW), (
        "RIVER_SEGMENT should place WATER_SHALLOW terrain"
    )


def test_river_segment_places_fish() -> None:
    """RiverSegmentTemplate should place river fish species."""
    mm, pc = _make_manager()
    mm.create_river_segment(pc)
    fish_placed = any(
        _specific_unit_placed(mm, fish)
        for fish in (
            OtherInfo.FISH_SALMON,
            OtherInfo.FISH_TUNA,
            OtherInfo.FISH_DORADO,
            OtherInfo.FISH_SNAPPER,
            OtherInfo.SHORE_FISH,
        )
    )
    assert fish_placed, "RIVER_SEGMENT should place at least one fish species"


def test_river_segment_empty_collection_no_crash() -> None:
    """RiverSegmentTemplate should not raise when given an empty collection."""
    mm = MapManager(60)
    mm.point_manager.add_point_collection("empty")
    empty_pc = mm.point_manager.get_point_collection("empty")
    # No points added — template should return safely
    mm.create_river_segment(empty_pc)
    assert True


# ---------------------------------------------------------------------------
# Pine forest
# ---------------------------------------------------------------------------

def test_pine_forest_places_pine_trees() -> None:
    """PineForestTemplate should place TREE_PINE_FOREST objects."""
    mm, pc = _make_manager()
    mm.create_pine_forest(pc, groups_density=0.05, group_size=10, clumping=3)
    assert _specific_unit_placed(mm, OtherInfo.TREE_PINE_FOREST), (
        "PINE_FOREST should place TREE_PINE_FOREST objects"
    )


def test_pine_forest_places_fauna() -> None:
    """PineForestTemplate should include deer, wolves, or bears."""
    mm, pc = _make_manager()
    mm.create_pine_forest(pc, groups_density=0.05, group_size=10, clumping=3)
    fauna_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (UnitInfo.DEER, UnitInfo.WOLF, UnitInfo.BEAR)
    )
    assert fauna_placed, "PINE_FOREST should place at least one woodland animal"


# ---------------------------------------------------------------------------
# Winter landscape
# ---------------------------------------------------------------------------

def test_winter_landscape_places_snow_terrain() -> None:
    """WinterLandscapeTemplate should place SNOW terrain."""
    mm, pc = _make_manager()
    mm.create_winter_landscape(pc, groups_density=0.04, group_size=8, clumping=3,
                                center_point=(40, 40), size=6)
    assert _specific_terrain_placed(mm, TerrainId.SNOW), (
        "WINTER_LANDSCAPE should place SNOW terrain"
    )


def test_winter_landscape_places_snow_pine_trees() -> None:
    """WinterLandscapeTemplate should place TREE_SNOW_PINE objects."""
    mm, pc = _make_manager()
    mm.create_winter_landscape(pc, groups_density=0.04, group_size=8, clumping=3,
                                center_point=(40, 40), size=6)
    assert _specific_unit_placed(mm, OtherInfo.TREE_SNOW_PINE), (
        "WINTER_LANDSCAPE should place TREE_SNOW_PINE objects"
    )


def test_winter_landscape_has_frozen_pond() -> None:
    """WinterLandscapeTemplate should place ICE terrain for the frozen pond."""
    mm, pc = _make_manager()
    mm.create_winter_landscape(pc, groups_density=0.04, group_size=8, clumping=3,
                                center_point=(40, 40), size=6)
    assert _specific_terrain_placed(mm, TerrainId.ICE), (
        "WINTER_LANDSCAPE should place ICE terrain for the frozen pond"
    )


def test_winter_landscape_has_arctic_animals() -> None:
    """WinterLandscapeTemplate should place wolves, snow leopards, or bears."""
    mm, pc = _make_manager()
    mm.create_winter_landscape(pc, groups_density=0.04, group_size=8, clumping=3,
                                center_point=(40, 40), size=5)
    animals_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (UnitInfo.WOLF, UnitInfo.SNOW_LEOPARD, UnitInfo.BEAR)
    )
    assert animals_placed, "WINTER_LANDSCAPE should place arctic animals"


# ---------------------------------------------------------------------------
# Desert
# ---------------------------------------------------------------------------

def test_desert_places_sand_terrain() -> None:
    """DesertTemplate should place DESERT_SAND terrain."""
    mm, pc = _make_manager()
    mm.create_desert(pc, groups_density=0.03, group_size=5, clumping=3)
    assert _specific_terrain_placed(mm, TerrainId.DESERT_SAND), (
        "DESERT should place DESERT_SAND terrain"
    )


def test_desert_places_palm_trees() -> None:
    """DesertTemplate should scatter TREE_PALM_FOREST objects."""
    mm, pc = _make_manager()
    mm.create_desert(pc, groups_density=0.03, group_size=5, clumping=3)
    assert _specific_unit_placed(mm, OtherInfo.TREE_PALM_FOREST), (
        "DESERT should place TREE_PALM_FOREST objects"
    )


def test_desert_places_desert_fauna() -> None:
    """DesertTemplate should place camels, lions, or vultures."""
    mm, pc = _make_manager()
    mm.create_desert(pc, groups_density=0.03, group_size=5, clumping=3)
    fauna_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (
            UnitInfo.WILD_BACTRIAN_CAMEL,
            UnitInfo.WILD_CAMEL,
            UnitInfo.LION,
            UnitInfo.VULTURE,
        )
    )
    assert fauna_placed, "DESERT should place at least one desert animal"


# ---------------------------------------------------------------------------
# Desert oasis
# ---------------------------------------------------------------------------

def test_desert_oasis_places_sand_terrain() -> None:
    """DesertOasisTemplate should maintain DESERT_SAND terrain as background."""
    mm, pc = _make_manager()
    mm.create_desert_oasis(pc, groups_density=0.02, group_size=4, clumping=3,
                           center_point=(40, 40), size=10)
    assert _specific_terrain_placed(mm, TerrainId.DESERT_SAND), (
        "DESERT_OASIS should place DESERT_SAND terrain"
    )


def test_desert_oasis_places_oasis_water() -> None:
    """DesertOasisTemplate should place SHALLOWS_AZURE terrain for the oasis."""
    mm, pc = _make_manager()
    mm.create_desert_oasis(pc, groups_density=0.02, group_size=4, clumping=3,
                           center_point=(40, 40), size=10)
    assert _specific_terrain_placed(mm, TerrainId.SHALLOWS_AZURE), (
        "DESERT_OASIS should place SHALLOWS_AZURE for the oasis pool"
    )


def test_desert_oasis_places_fish_in_oasis() -> None:
    """DesertOasisTemplate should place fish in the oasis water."""
    mm, pc = _make_manager()
    mm.create_desert_oasis(pc, groups_density=0.02, group_size=4, clumping=3,
                           center_point=(40, 40), size=10)
    fish_placed = any(
        _specific_unit_placed(mm, fish)
        for fish in (
            OtherInfo.FISH_DORADO,
            OtherInfo.FISH_PERCH,
            OtherInfo.SHORE_FISH,
            OtherInfo.BOX_TURTLES,
        )
    )
    assert fish_placed, "DESERT_OASIS should place fish in the oasis"


# ---------------------------------------------------------------------------
# Savannah
# ---------------------------------------------------------------------------

def test_savannah_places_dry_terrain() -> None:
    """SavannahTemplate should place GRASS_DRY terrain."""
    mm, pc = _make_manager()
    mm.create_savannah(pc, groups_density=0.02, group_size=3, clumping=2)
    assert _specific_terrain_placed(mm, TerrainId.GRASS_DRY), (
        "SAVANNAH should place GRASS_DRY terrain"
    )


def test_savannah_places_acacia_trees() -> None:
    """SavannahTemplate should scatter TREE_ACACIA objects."""
    mm, pc = _make_manager()
    mm.create_savannah(pc, groups_density=0.02, group_size=3, clumping=2)
    assert _specific_unit_placed(mm, OtherInfo.TREE_ACACIA), (
        "SAVANNAH should place TREE_ACACIA trees"
    )


def test_savannah_places_savannah_fauna() -> None:
    """SavannahTemplate should place zebras, ostriches, lions, or rhinos."""
    mm, pc = _make_manager()
    mm.create_savannah(pc, groups_density=0.02, group_size=3, clumping=2)
    fauna_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (
            UnitInfo.ZEBRA,
            UnitInfo.OSTRICH,
            UnitInfo.RHINOCEROS,
            UnitInfo.LION,
            UnitInfo.IBEX,
        )
    )
    assert fauna_placed, "SAVANNAH should place savannah fauna"


# ---------------------------------------------------------------------------
# Rainforest
# ---------------------------------------------------------------------------

def test_rainforest_places_jungle_terrain() -> None:
    """RainforestTemplate should place GRASS_JUNGLE terrain."""
    mm, pc = _make_manager()
    mm.create_rainforest(pc, groups_density=0.05, group_size=12, clumping=5)
    assert _specific_terrain_placed(mm, TerrainId.GRASS_JUNGLE), (
        "RAINFOREST should place GRASS_JUNGLE terrain"
    )


def test_rainforest_places_rainforest_trees() -> None:
    """RainforestTemplate should place TREE_RAINFOREST objects."""
    mm, pc = _make_manager()
    mm.create_rainforest(pc, groups_density=0.05, group_size=12, clumping=5)
    assert _specific_unit_placed(mm, OtherInfo.TREE_RAINFOREST), (
        "RAINFOREST should place TREE_RAINFOREST objects"
    )


def test_rainforest_places_rainforest_fauna() -> None:
    """RainforestTemplate should place jaguars, macaws, or storks."""
    mm, pc = _make_manager()
    mm.create_rainforest(pc, groups_density=0.05, group_size=12, clumping=5)
    fauna_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (UnitInfo.JAGUAR, UnitInfo.MACAW, UnitInfo.STORK)
    )
    assert fauna_placed, "RAINFOREST should place at least one rainforest animal"


# ---------------------------------------------------------------------------
# Mediterranean
# ---------------------------------------------------------------------------

def test_mediterranean_places_grass_terrain() -> None:
    """MediterraneanTemplate should place GRASS_2 terrain."""
    mm, pc = _make_manager()
    mm.create_mediterranean(pc, groups_density=0.04, group_size=7, clumping=3)
    assert _specific_terrain_placed(mm, TerrainId.GRASS_2), (
        "MEDITERRANEAN should place GRASS_2 terrain"
    )


def test_mediterranean_places_olive_trees() -> None:
    """MediterraneanTemplate should place TREE_OLIVE objects."""
    mm, pc = _make_manager()
    mm.create_mediterranean(pc, groups_density=0.04, group_size=7, clumping=3)
    assert _specific_unit_placed(mm, OtherInfo.TREE_OLIVE), (
        "MEDITERRANEAN should place TREE_OLIVE objects"
    )


def test_mediterranean_places_temperate_fauna() -> None:
    """MediterraneanTemplate should place deer, wild boar, or bears."""
    mm, pc = _make_manager()
    mm.create_mediterranean(pc, groups_density=0.04, group_size=7, clumping=3)
    fauna_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (UnitInfo.DEER, UnitInfo.WILD_BOAR, UnitInfo.BEAR)
    )
    assert fauna_placed, "MEDITERRANEAN should place temperate woodland fauna"


# ---------------------------------------------------------------------------
# apply_template API round-trip tests
# ---------------------------------------------------------------------------

def test_apply_template_pond() -> None:
    """TemplateType.POND should be callable via apply_template."""
    mm, pc = _make_manager()
    center = (40, 40)
    config = TemplateConfig(
        point_collection=pc,
        center_point=center,
        size=8,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.POND, config=config,
                      center_point=center, size=8)
    assert _specific_terrain_placed(mm, TerrainId.SHALLOWS), (
        "apply_template(POND) should place SHALLOWS terrain"
    )


def test_apply_template_river_segment() -> None:
    """TemplateType.RIVER_SEGMENT should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.RIVER_SEGMENT, config=config)
    assert _specific_terrain_placed(mm, TerrainId.WATER_SHALLOW), (
        "apply_template(RIVER_SEGMENT) should place WATER_SHALLOW terrain"
    )


def test_apply_template_pine_forest() -> None:
    """TemplateType.PINE_FOREST should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.PINE_FOREST, config=config,
                      groups_density=0.05, group_size=10, clumping=3)
    assert _specific_unit_placed(mm, OtherInfo.TREE_PINE_FOREST), (
        "apply_template(PINE_FOREST) should place TREE_PINE_FOREST"
    )


def test_apply_template_snow_forest() -> None:
    """TemplateType.SNOW_FOREST should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.SNOW_FOREST, config=config,
                      groups_density=0.05, group_size=8, clumping=3)
    assert _specific_unit_placed(mm, OtherInfo.TREE_SNOW_PINE), (
        "apply_template(SNOW_FOREST) should place TREE_SNOW_PINE"
    )


def test_apply_template_winter_landscape() -> None:
    """TemplateType.WINTER_LANDSCAPE should be callable via apply_template."""
    mm, pc = _make_manager()
    center = (40, 40)
    config = TemplateConfig(
        point_collection=pc,
        center_point=center,
        size=6,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.WINTER_LANDSCAPE, config=config,
                      groups_density=0.04, group_size=8, clumping=3,
                      center_point=center, size=6)
    assert _specific_terrain_placed(mm, TerrainId.SNOW), (
        "apply_template(WINTER_LANDSCAPE) should place SNOW terrain"
    )


def test_apply_template_desert() -> None:
    """TemplateType.DESERT should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.DESERT, config=config,
                      groups_density=0.03, group_size=5, clumping=3)
    assert _specific_terrain_placed(mm, TerrainId.DESERT_SAND), (
        "apply_template(DESERT) should place DESERT_SAND terrain"
    )


def test_apply_template_savannah() -> None:
    """TemplateType.SAVANNAH should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.SAVANNAH, config=config,
                      groups_density=0.02, group_size=3, clumping=2)
    assert _specific_terrain_placed(mm, TerrainId.GRASS_DRY), (
        "apply_template(SAVANNAH) should place GRASS_DRY terrain"
    )


def test_apply_template_rainforest() -> None:
    """TemplateType.RAINFOREST should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.RAINFOREST, config=config,
                      groups_density=0.05, group_size=12, clumping=5)
    assert _specific_terrain_placed(mm, TerrainId.GRASS_JUNGLE), (
        "apply_template(RAINFOREST) should place GRASS_JUNGLE terrain"
    )


def test_apply_template_mediterranean() -> None:
    """TemplateType.MEDITERRANEAN should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        size=0,
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.MEDITERRANEAN, config=config,
                      groups_density=0.04, group_size=7, clumping=3)
    assert _specific_terrain_placed(mm, TerrainId.GRASS_2), (
        "apply_template(MEDITERRANEAN) should place GRASS_2 terrain"
    )
