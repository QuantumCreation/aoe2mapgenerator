"""Named map recipes shared by the CLI tools, tests, and (later) the frontend.

A *recipe* is a small, self-contained builder function that takes a fresh
``MapManager`` and produces a complete map. Keeping recipes as plain functions
in one registry means:

- ``tools/evaluate_map.py`` and ``tools/render_map.py`` build the exact same
  map the tests do (no drift).
- The frontend "Quick Start" can later enumerate ``RECIPE_NAMES`` and call the
  same builders through the backend.

Each recipe is deterministic for a given seed because it draws all randomness
from the ``MapManager``'s seeded RNG.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

from aoe2mapgenerator import (
    GateType,
    MapLayerType,
    MapManager,
    PerlinNoiseConfig,
    PerlinTerrainConfig,
    PerlinTerrainGenerator,
    PlaceGroupsConfig,
    TerrainBand,
)
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.templates_manager import TemplateConfig


@dataclass(frozen=True)
class Recipe:
    """A named, parameterized map builder."""

    name: str
    description: str
    build: Callable[["MapManager", int], None]
    map_size: int = 120
    # Optional layer to run the evenness metric on (e.g. DECOR for forests).
    scatter_layer: MapLayerType | None = None


def _grass_base(mg: MapManager, seed: int = 0) -> None:
    """Fill the whole map with a Perlin-blended grass/dirt terrain base.

    ``place_groups`` is a *clustering* placer (it scatters groups), so it is
    the wrong tool for a full base fill. Perlin terrain classifies every tile,
    giving a complete, natural-looking ground layer.

    Note: the lowest band uses ``GRASS_OTHER`` (id 16) rather than ``GRASS_1``
    (id 0). Terrain id 0 collides with the empty sentinel
    (``DEFAULT_EMPTY_OBJECT = MapObject(0, GAIA)``), so ``GRASS_1`` tiles are
    indistinguishable from empty and would render as dark gaps.
    """
    bands = (
        TerrainBand(max_noise=0.30, terrain_id=TerrainId.GRASS_OTHER),
        TerrainBand(max_noise=0.60, terrain_id=TerrainId.GRASS_2),
        TerrainBand(max_noise=0.85, terrain_id=TerrainId.GRASS_3),
        TerrainBand(max_noise=1.00, terrain_id=TerrainId.DIRT_1),
    )
    config = PerlinTerrainConfig(
        noise=PerlinNoiseConfig(seed=seed, scale=40.0, octaves=5),
        terrain_bands=bands,
        min_elevation=0,
        max_elevation=3,
    )
    PerlinTerrainGenerator(mg.map).generate_perlin_terrain(config)


def _region(mg: MapManager, name: str, x0: int, y0: int, x1: int, y1: int):
    """Add a rectangular point collection, clamped to map bounds."""
    size = mg.map.size
    mg.point_manager.add_point_collection(name)
    pc = mg.point_manager.get_point_collection(name)
    pc.add_points(
        [
            (x, y)
            for x in range(max(0, x0), min(size, x1))
            for y in range(max(0, y0), min(size, y1))
        ]
    )
    return pc


# ---------------------------------------------------------------------------
# Recipe builders
# ---------------------------------------------------------------------------


def _build_city(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    city_pts = _region(mg, "city_region", 20, 20, 100, 100)
    mg.create_city(
        point_collection=city_pts,
        center_point=(60, 60),
        size=40,
        player_id=PlayerId.ONE,
        gate_type=GateType.CITY_GATE,
    )
    for i, (cx, cy) in enumerate([(5, 5), (5, 105), (105, 5), (105, 105)]):
        fp = _region(mg, f"forest_{i}", cx - 8, cy - 8, cx + 8, cy + 8)
        mg.create_oak_forest(
            point_collection=fp, groups_density=0.08, group_size=8, clumping=3
        )


def _build_fort(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    fort_pts = _region(mg, "fort_region", 30, 30, 90, 90)
    mg.create_fort(
        point_collection=fort_pts,
        center_point=(60, 60),
        size=25,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )


def _build_village(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    village_pts = _region(mg, "village_region", 30, 30, 90, 90)
    mg.apply_template(
        village_pts,
        TemplateType.VILLAGE,
        config=TemplateConfig(
            point_collection=village_pts,
            center_point=(60, 60),
            size=20,
            player_id=PlayerId.ONE,
        ),
    )


def _build_forest(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    forest_pts = _region(mg, "forest_region", 0, 0, 120, 120)
    mg.create_oak_forest(
        point_collection=forest_pts,
        groups_density=0.05,
        group_size=10,
        clumping=4,
    )


def _build_fauna(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    pts = _region(mg, "fauna_region", 0, 0, 120, 120)
    mg.create_fauna_scatter(
        point_collection=pts, herd_count=8, predator_count=4, herd_size=(3, 6)
    )


def _build_berries(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    pts = _region(mg, "berry_region", 0, 0, 120, 120)
    mg.create_berry_bush(point_collection=pts, density=0.03)


def _build_bandit_camp(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    pts = _region(mg, "camp_region", 20, 20, 100, 100)
    mg.create_bandit_camp(
        point_collection=pts, center_point=(60, 60), size=14, tents=6, bandits=8
    )


def _build_snowy_mountains(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    # Elongated region so the ridge reads as a range, not a blob.
    pts = _region(mg, "range_region", 10, 35, 110, 85)
    mg.create_snowy_mountain_range(point_collection=pts, max_elevation=6)


def _build_lush_forest(mg: MapManager, seed: int) -> None:
    _grass_base(mg, seed)
    pts = _region(mg, "lush_region", 0, 0, 120, 120)
    mg.create_lush_forest(point_collection=pts, tree_density=0.15, clearings=4)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RECIPES: dict[str, Recipe] = {
    r.name: r
    for r in [
        Recipe(
            name="city",
            description="Walled city with districts, gates, roads + corner forests",
            build=_build_city,
        ),
        Recipe(
            name="fort",
            description="Fortified square with walls and gates",
            build=_build_fort,
        ),
        Recipe(
            name="village",
            description="Small village settlement",
            build=_build_village,
        ),
        Recipe(
            name="forest",
            description="Oak forest scatter (evenness showcase)",
            build=_build_forest,
            # Oak trees are placed on the UNIT layer (alongside fauna/bushes).
            scatter_layer=MapLayerType.UNIT,
        ),
        Recipe(
            name="fauna",
            description="Wild animal herds and lone predators",
            build=_build_fauna,
            # No evenness metric: herds are intentionally clustered, so
            # nearest-neighbour uniformity is the wrong measure here.
        ),
        Recipe(
            name="berries",
            description="Forage / fruit bush scatter (berry patch)",
            build=_build_berries,
            scatter_layer=MapLayerType.UNIT,
        ),
        Recipe(
            name="bandit_camp",
            description="Hostile camp: dirt patch, bonfire, tent ring, bandits",
            build=_build_bandit_camp,
        ),
        Recipe(
            name="snowy_mountains",
            description="Elongated snow-mountain ridgeline with elevation",
            build=_build_snowy_mountains,
        ),
        Recipe(
            name="lush_forest",
            description="Dense mixed forest with berries, fauna, and clearings",
            build=_build_lush_forest,
            scatter_layer=MapLayerType.UNIT,
        ),
    ]
}

RECIPE_NAMES: list[str] = list(RECIPES.keys())


def build_recipe(name: str, seed: int = 0, map_size: int | None = None) -> MapManager:
    """Build a named recipe and return the populated ``MapManager``.

    Args:
        name: A key in :data:`RECIPES`.
        seed: RNG seed (deterministic per seed).
        map_size: Override the recipe's default map size.

    Returns:
        The built ``MapManager``.
    """
    if name not in RECIPES:
        raise KeyError(f"Unknown recipe {name!r}. Available: {RECIPE_NAMES}")
    recipe = RECIPES[name]
    size = map_size or recipe.map_size
    mg = MapManager(size, output_dir="/tmp", seed=seed)
    recipe.build(mg, seed)
    return mg
