"""Golden-seed regression tests for the named map recipes.

These pin the *quality* and *determinism* of every recipe at a fixed set of
seeds. They are the automated gate for the iteration loop: a generation change
is not reviewed visually until these pass.

For each (recipe, seed) pair the test asserts:
  1. The recipe builds without raising.
  2. The headless quality report passes (no hard FAIL metric).
  3. The build is deterministic: rebuilding with the same seed reproduces the
     exact per-layer object counts.

The seeds are small and fixed on purpose — they are the "golden" seeds. If a
change legitimately alters a recipe's output, update the expectations here and
note the reason in the commit message.
"""

import pytest

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.evaluation.metrics import compute_report
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.recipes import RECIPE_NAMES, build_recipe

# The fixed "golden" seeds. Kept small and stable.
GOLDEN_SEEDS = [1, 7, 42]

# Recipes that guarantee per-seed determinism. These draw all randomness from
# the MapManager's seeded RNG (and a numpy Generator seeded with the same seed).
#
# The older structural recipes (city, fort, village) are built with the
# ``place_groups`` group placer, which draws from the *global* ``random`` module
# rather than the seeded manager RNG, so they are intentionally excluded from
# the determinism assertion (they are still covered by the metrics test above).
DETERMINISTIC_RECIPES = [
    "fauna",
    "berries",
    "bandit_camp",
    "snowy_mountains",
    "lush_forest",
]

# Layers whose object counts we pin for determinism.
_COUNTED_LAYERS = (
    MapLayerType.TERRAIN,
    MapLayerType.DECOR,
    MapLayerType.UNIT,
    MapLayerType.ELEVATION,
)


def _layer_counts(mg: MapManager) -> dict[MapLayerType, int]:
    """Return the number of non-empty tiles on each counted layer."""
    counts: dict[MapLayerType, int] = {}
    for layer in _COUNTED_LAYERS:
        tiles = mg.get_dictionary(layer)
        counts[layer] = sum(1 for v in tiles.values() if v is not None)
    return counts


@pytest.mark.parametrize("recipe_name", RECIPE_NAMES)
@pytest.mark.parametrize("seed", GOLDEN_SEEDS)
def test_recipe_builds_and_passes_metrics(recipe_name: str, seed: int) -> None:
    """Every recipe at every golden seed should build and pass its quality report."""
    mg = build_recipe(recipe_name, seed=seed)
    report = compute_report(mg)
    assert report.all_pass(), (
        f"Recipe {recipe_name!r} (seed {seed}) failed quality metrics:\n"
        f"{report.to_text()}"
    )


@pytest.mark.parametrize("recipe_name", DETERMINISTIC_RECIPES)
@pytest.mark.parametrize("seed", GOLDEN_SEEDS)
def test_recipe_is_deterministic_per_seed(recipe_name: str, seed: int) -> None:
    """Rebuilding a deterministic recipe with the same seed must reproduce identical layer counts."""
    mg_a = build_recipe(recipe_name, seed=seed)
    mg_b = build_recipe(recipe_name, seed=seed)
    counts_a = _layer_counts(mg_a)
    counts_b = _layer_counts(mg_b)
    assert counts_a == counts_b, (
        f"Recipe {recipe_name!r} (seed {seed}) is not deterministic:\n"
        f"  first build:  {counts_a}\n"
        f"  second build: {counts_b}"
    )
