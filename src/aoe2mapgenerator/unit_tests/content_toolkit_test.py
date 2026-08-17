"""Unit tests for the map-content toolkit templates.

Each test verifies:
  1. The operation completes without raising.
  2. Expected terrain or object types appear on the correct map layer.
  3. (Where relevant) determinism: the same seed reproduces the same layout.

Templates tested:
  - FaunaScatterTemplate        (FAUNA_SCATTER)
  - BerryBushTemplate           (BERRY_BUSH)
  - BanditCampTemplate          (BANDIT_CAMP)
  - SnowyMountainRangeTemplate  (SNOWY_MOUNTAIN_RANGE)
  - LushForestTemplate          (LUSH_FOREST)

MapManager convenience helpers tested:
  create_fauna_scatter, create_berry_bush, create_bandit_camp,
  create_snowy_mountain_range, create_lush_forest.
"""

from typing import Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
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

def _make_manager(
    n: int = 80,
    x0: int = 0,
    y0: int = 0,
    x1: int | None = None,
    y1: int | None = None,
    seed: int = 1,
) -> "tuple[MapManager, PointCollection]":
    """Return a fresh *n*×*n* MapManager with a PointCollection over [x0,x1)×[y0,y1).

    Defaults to full coverage. Pass ``seed`` to control the manager's RNG.
    """
    x1 = n if x1 is None else x1
    y1 = n if y1 is None else y1
    mm = MapManager(n, seed=seed)
    mm.point_manager.add_point_collection("pts")
    mm.point_manager.get_point_collection("pts").add_points(
        [(i, j) for i in range(x0, x1) for j in range(y0, y1)]
    )
    return mm, mm.point_manager.get_point_collection("pts")


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


def _unit_count(map_manager: MapManager) -> int:
    """Return the number of non-empty tiles on the UNIT layer."""
    units = map_manager.get_dictionary(MapLayerType.UNIT)
    return sum(1 for v in units.values() if v is not None)


def _max_elevation(map_manager: MapManager) -> int:
    """Return the maximum elevation value stored on the ELEVATION layer."""
    elev = map_manager.get_map_layer(MapLayerType.ELEVATION)
    size = map_manager.map.size
    best = 0
    for x in range(size):
        for y in range(size):
            best = max(best, int(elev.get_object_at_point((x, y)).obj_type))
    return best


# ---------------------------------------------------------------------------
# Fauna scatter
# ---------------------------------------------------------------------------

def test_fauna_scatter_places_herd_animals() -> None:
    """FAUNA_SCATTER should place grazing herd animals (e.g. deer)."""
    mm, pc = _make_manager()
    mm.create_fauna_scatter(pc, herd_count=6, predator_count=3)
    assert _specific_unit_placed(mm, UnitInfo.DEER), (
        "FAUNA_SCATTER should place at least one DEER"
    )


def test_fauna_scatter_places_predators() -> None:
    """FAUNA_SCATTER should place lone predators (wolf / bear / dire wolf)."""
    mm, pc = _make_manager()
    mm.create_fauna_scatter(pc, herd_count=6, predator_count=3)
    predator_placed = any(
        _specific_unit_placed(mm, animal)
        for animal in (UnitInfo.WOLF, UnitInfo.BEAR, UnitInfo.DIRE_WOLF)
    )
    assert predator_placed, "FAUNA_SCATTER should place at least one predator"


def test_fauna_scatter_empty_collection_no_crash() -> None:
    """FAUNA_SCATTER should return safely on an empty collection."""
    mm = MapManager(60)
    mm.point_manager.add_point_collection("empty")
    empty_pc = mm.point_manager.get_point_collection("empty")
    mm.create_fauna_scatter(empty_pc)
    assert True


# ---------------------------------------------------------------------------
# Berry bush
# ---------------------------------------------------------------------------

def test_berry_bush_places_bushes() -> None:
    """BERRY_BUSH should place forage / fruit bushes on the UNIT layer."""
    mm, pc = _make_manager()
    mm.create_berry_bush(pc, density=0.03)
    bush_placed = any(
        _specific_unit_placed(mm, bush)
        for bush in (
            OtherInfo.FORAGE_BUSH,
            OtherInfo.FRUIT_BUSH,
            OtherInfo.BUSH_A,
            OtherInfo.BUSH_B,
            OtherInfo.BUSH_C,
        )
    )
    assert bush_placed, "BERRY_BUSH should place at least one bush"


def test_berry_bush_places_multiple_varieties() -> None:
    """BERRY_BUSH should mix more than one bush variety."""
    mm, pc = _make_manager()
    mm.create_berry_bush(pc, density=0.03)
    varieties = sum(
        1
        for bush in (
            OtherInfo.FORAGE_BUSH,
            OtherInfo.FRUIT_BUSH,
            OtherInfo.BUSH_A,
            OtherInfo.BUSH_B,
            OtherInfo.BUSH_C,
        )
        if _specific_unit_placed(mm, bush)
    )
    assert varieties >= 2, "BERRY_BUSH should place at least two bush varieties"


# ---------------------------------------------------------------------------
# Bandit camp
# ---------------------------------------------------------------------------

def test_bandit_camp_places_dirt_terrain() -> None:
    """BANDIT_CAMP should paint a circular DIRT_1 terrain patch."""
    mm, pc = _make_manager()
    mm.create_bandit_camp(pc, center_point=(40, 40), size=10)
    assert _specific_terrain_placed(mm, TerrainId.DIRT_1), (
        "BANDIT_CAMP should place DIRT_1 terrain"
    )


def test_bandit_camp_places_bonfire() -> None:
    """BANDIT_CAMP should place a central BONFIRE."""
    mm, pc = _make_manager()
    mm.create_bandit_camp(pc, center_point=(40, 40), size=10)
    assert _specific_unit_placed(mm, OtherInfo.BONFIRE), (
        "BANDIT_CAMP should place a BONFIRE"
    )


def test_bandit_camp_places_tents() -> None:
    """BANDIT_CAMP should place a ring of tents (TENT_A–TENT_E)."""
    mm, pc = _make_manager()
    mm.create_bandit_camp(pc, center_point=(40, 40), size=10, tents=5)
    tent_placed = any(
        _specific_unit_placed(mm, tent)
        for tent in (
            BuildingInfo.TENT_A,
            BuildingInfo.TENT_B,
            BuildingInfo.TENT_C,
            BuildingInfo.TENT_D,
            BuildingInfo.TENT_E,
        )
    )
    assert tent_placed, "BANDIT_CAMP should place at least one tent"


def test_bandit_camp_places_bandits() -> None:
    """BANDIT_CAMP should scatter BANDIT units around the camp."""
    mm, pc = _make_manager()
    mm.create_bandit_camp(pc, center_point=(40, 40), size=10, bandits=6)
    assert _specific_unit_placed(mm, UnitInfo.BANDIT), (
        "BANDIT_CAMP should place at least one BANDIT"
    )


# ---------------------------------------------------------------------------
# Snowy mountain range
# ---------------------------------------------------------------------------

def test_snowy_mountain_range_places_snow_terrain() -> None:
    """SNOWY_MOUNTAIN_RANGE should paint SNOW terrain across the region."""
    mm, pc = _make_manager(n=120, x0=10, x1=110, y0=35, y1=85)
    mm.create_snowy_mountain_range(pc, max_elevation=6)
    assert _specific_terrain_placed(mm, TerrainId.SNOW), (
        "SNOWY_MOUNTAIN_RANGE should place SNOW terrain"
    )


def test_snowy_mountain_range_places_mountain_objects() -> None:
    """SNOWY_MOUNTAIN_RANGE should scatter SNOW_MOUNTAIN objects on high ground."""
    mm, pc = _make_manager(n=120, x0=10, x1=110, y0=35, y1=85)
    mm.create_snowy_mountain_range(pc, max_elevation=6)
    mountain_placed = any(
        _specific_unit_placed(mm, mountain)
        for mountain in (
            OtherInfo.SNOW_MOUNTAIN_1,
            OtherInfo.SNOW_MOUNTAIN_2,
            OtherInfo.SNOW_MOUNTAIN_3,
        )
    )
    assert mountain_placed, (
        "SNOWY_MOUNTAIN_RANGE should place at least one SNOW_MOUNTAIN object"
    )


def test_snowy_mountain_range_sets_elevation() -> None:
    """SNOWY_MOUNTAIN_RANGE should set non-zero elevation along the ridge."""
    mm, pc = _make_manager(n=120, x0=10, x1=110, y0=35, y1=85)
    mm.create_snowy_mountain_range(pc, max_elevation=6)
    assert _max_elevation(mm) >= 3, (
        "SNOWY_MOUNTAIN_RANGE should set elevation >= 3 near the ridge"
    )


# ---------------------------------------------------------------------------
# Lush forest
# ---------------------------------------------------------------------------

def test_lush_forest_places_trees() -> None:
    """LUSH_FOREST should place a mix of tree species."""
    mm, pc = _make_manager()
    mm.create_lush_forest(pc, tree_density=0.15, clearings=3)
    tree_placed = any(
        _specific_unit_placed(mm, tree)
        for tree in (
            OtherInfo.TREE_OAK,
            OtherInfo.TREE_OAK_FOREST,
            OtherInfo.TREE_PINE_FOREST,
            OtherInfo.TREE_OAK_AUTUMN,
        )
    )
    assert tree_placed, "LUSH_FOREST should place at least one tree"


def test_lush_forest_places_berry_bushes() -> None:
    """LUSH_FOREST should scatter berry bushes in the undergrowth."""
    mm, pc = _make_manager()
    mm.create_lush_forest(pc, tree_density=0.15, clearings=3)
    bush_placed = any(
        _specific_unit_placed(mm, bush)
        for bush in (OtherInfo.FORAGE_BUSH, OtherInfo.FRUIT_BUSH, OtherInfo.BUSH_A)
    )
    assert bush_placed, "LUSH_FOREST should place at least one berry bush"


def test_lush_forest_places_fauna() -> None:
    """LUSH_FOREST should place a handful of deer."""
    mm, pc = _make_manager()
    mm.create_lush_forest(pc, tree_density=0.15, clearings=3)
    assert _specific_unit_placed(mm, UnitInfo.DEER), (
        "LUSH_FOREST should place at least one DEER"
    )


# ---------------------------------------------------------------------------
# apply_template API round-trip tests
# ---------------------------------------------------------------------------

def test_apply_template_fauna_scatter() -> None:
    """TemplateType.FAUNA_SCATTER should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.FAUNA_SCATTER, config=config,
                      herd_count=6, predator_count=3)
    assert _specific_unit_placed(mm, UnitInfo.DEER), (
        "apply_template(FAUNA_SCATTER) should place DEER"
    )


def test_apply_template_berry_bush() -> None:
    """TemplateType.BERRY_BUSH should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.BERRY_BUSH, config=config, density=0.03)
    assert any(
        _specific_unit_placed(mm, bush)
        for bush in (OtherInfo.FORAGE_BUSH, OtherInfo.FRUIT_BUSH, OtherInfo.BUSH_A)
    ), "apply_template(BERRY_BUSH) should place at least one bush"


def test_apply_template_bandit_camp() -> None:
    """TemplateType.BANDIT_CAMP should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.BANDIT_CAMP, config=config,
                      center_point=(40, 40), size=10, tents=5, bandits=6)
    assert _specific_unit_placed(mm, OtherInfo.BONFIRE), (
        "apply_template(BANDIT_CAMP) should place a BONFIRE"
    )


def test_apply_template_snowy_mountain_range() -> None:
    """TemplateType.SNOWY_MOUNTAIN_RANGE should be callable via apply_template."""
    mm, pc = _make_manager(n=120, x0=10, x1=110, y0=35, y1=85)
    config = TemplateConfig(
        point_collection=pc,
        center_point=(60, 60),
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.SNOWY_MOUNTAIN_RANGE, config=config,
                      max_elevation=6)
    assert _specific_terrain_placed(mm, TerrainId.SNOW), (
        "apply_template(SNOWY_MOUNTAIN_RANGE) should place SNOW terrain"
    )


def test_apply_template_lush_forest() -> None:
    """TemplateType.LUSH_FOREST should be callable via apply_template."""
    mm, pc = _make_manager()
    config = TemplateConfig(
        point_collection=pc,
        center_point=(40, 40),
        player_id=PlayerId.GAIA,
    )
    mm.apply_template(pc, TemplateType.LUSH_FOREST, config=config,
                      tree_density=0.15, clearings=3)
    assert any(
        _specific_unit_placed(mm, tree)
        for tree in (
            OtherInfo.TREE_OAK,
            OtherInfo.TREE_OAK_FOREST,
            OtherInfo.TREE_PINE_FOREST,
            OtherInfo.TREE_OAK_AUTUMN,
        )
    ), "apply_template(LUSH_FOREST) should place at least one tree"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_fauna_scatter_deterministic_per_seed() -> None:
    """FAUNA_SCATTER with the same seed should reproduce the same unit count."""
    mm_a, pc_a = _make_manager(seed=42)
    mm_b, pc_b = _make_manager(seed=42)
    mm_a.create_fauna_scatter(pc_a, herd_count=8, predator_count=4)
    mm_b.create_fauna_scatter(pc_b, herd_count=8, predator_count=4)
    assert _unit_count(mm_a) == _unit_count(mm_b), (
        "FAUNA_SCATTER should be deterministic for a fixed seed"
    )


def test_berry_bush_deterministic_per_seed() -> None:
    """BERRY_BUSH with the same seed should reproduce the same unit count."""
    mm_a, pc_a = _make_manager(seed=7)
    mm_b, pc_b = _make_manager(seed=7)
    mm_a.create_berry_bush(pc_a, density=0.03)
    mm_b.create_berry_bush(pc_b, density=0.03)
    assert _unit_count(mm_a) == _unit_count(mm_b), (
        "BERRY_BUSH should be deterministic for a fixed seed"
    )


def test_bandit_camp_deterministic_per_seed() -> None:
    """BANDIT_CAMP with the same seed should reproduce the same unit count."""
    mm_a, pc_a = _make_manager(seed=99)
    mm_b, pc_b = _make_manager(seed=99)
    mm_a.create_bandit_camp(pc_a, center_point=(40, 40), size=12, tents=6, bandits=8)
    mm_b.create_bandit_camp(pc_b, center_point=(40, 40), size=12, tents=6, bandits=8)
    assert _unit_count(mm_a) == _unit_count(mm_b), (
        "BANDIT_CAMP should be deterministic for a fixed seed"
    )


def test_snowy_mountain_range_deterministic_per_seed() -> None:
    """SNOWY_MOUNTAIN_RANGE with the same seed should reproduce the same layout."""
    mm_a, pc_a = _make_manager(n=120, x0=10, x1=110, y0=35, y1=85, seed=5)
    mm_b, pc_b = _make_manager(n=120, x0=10, x1=110, y0=35, y1=85, seed=5)
    mm_a.create_snowy_mountain_range(pc_a, max_elevation=6)
    mm_b.create_snowy_mountain_range(pc_b, max_elevation=6)
    assert _unit_count(mm_a) == _unit_count(mm_b), (
        "SNOWY_MOUNTAIN_RANGE should be deterministic for a fixed seed"
    )
    assert _max_elevation(mm_a) == _max_elevation(mm_b), (
        "SNOWY_MOUNTAIN_RANGE elevation should be deterministic for a fixed seed"
    )


def test_lush_forest_deterministic_per_seed() -> None:
    """LUSH_FOREST with the same seed should reproduce the same unit count."""
    mm_a, pc_a = _make_manager(seed=123)
    mm_b, pc_b = _make_manager(seed=123)
    mm_a.create_lush_forest(pc_a, tree_density=0.15, clearings=4)
    mm_b.create_lush_forest(pc_b, tree_density=0.15, clearings=4)
    assert _unit_count(mm_a) == _unit_count(mm_b), (
        "LUSH_FOREST should be deterministic for a fixed seed"
    )
