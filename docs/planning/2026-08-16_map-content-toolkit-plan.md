# Map Content Toolkit — Plan

Date: 2026-08-16
Status: DRAFT — pending prioritization feedback

## Goal

Make it fast and easy to create *interesting* AoE2 maps: one or two calls should
produce a coherent scene (terrain + settlements + resources + fauna +
decorations), with variety knobs so repeated use doesn't produce clones.

## Current State (what we build on)

| Capability | Where | Notes |
|---|---|---|
| City (districts, walls, gates, roads) | `templates/city*.py`, `MapManager.create_city` | Presets: compact / balanced / mega_city |
| Fort (6 shapes, towers, garrison) | `templates/fort.py`, `MapManager.create_fort` | square, rectangle, octagon, star, voronoi, grammar |
| Village (TC, farms, barracks, gaia, villagers) | `templates/village.py` | Single fixed layout |
| Palace, Castle, Mine, Mountain, Road, Walls, River, Pond | `MapManager.create_*` | Primitives |
| Nature biomes | `templates/nature.py`, `templates/decor.py` | Pine, Winter, Desert, Oasis, Savannah, Rainforest, Mediterranean, Oak, Snow |
| Perlin terrain + elevation | `terrain/terrain.py` | Terrain bands, elevation mapping |
| Wall shape generators | `units/wallgenerators/` | blocklord, polygon, perlin, voronoi, fort_shapes |
| Placers | `units/placers/` | groups, gates, paths, walls, voronoi |
| Frontend editor | `GeneralWebsite/frontend/.../AoE2MapGenerator` | Canvas, templates tab, zones, scenario config, triggers, saved user templates |

All templates follow the `AbstractTemplate` + `@register_template` pattern and
are exposed via `MapManager.create_*` convenience methods. New content = new
template class + manager method (+ optional frontend exposure).

## Gaps (what we want)

1. **Bandit camps** — missing entirely (tents, campfire, loot, bandit units, optional ambush triggers)
2. **Berry bushes** — no berry placement anywhere
3. **Generic fauna scatter** — deer/boar/wolves/sheep only hardcoded inside specific biomes; no standalone "scatter animals" tool
4. **Snowy mountain range** — `WinterLandscape` (flat snow) and `create_mountain` exist separately; no combined elevated snowy biome
5. **City variety** — one visual style; no trading / military / religious / port distinctions
6. **Village variety** — one layout; no fishing / farming / nomad-camp variants, no size tiers
7. **Fortress tier** — fort exists but no heavier variant (outer bailey, moat, double walls)
8. **Composition layer** — building a good map today = 8–15 chained calls; no "recipe" that composes terrain + settlements + resources in one call with a seed

## Proposed Design

### Layer 1 — New primitive templates (small, composable)

Each is a `AbstractTemplate` subclass registered via `@register_template`,
plus a `MapManager.create_*` wrapper. All accept `point_collection`,
`center_point` (defaults to centroid), `seed`-aware randomness, and density
knobs.

| Template | Contents |
|---|---|
| `BanditCampTemplate` | 3–6 tents, campfire, loot crates, watchtower, bandit units (scouts + archers + melee), optional patrol/ambush trigger hook |
| `BerryBushTemplate` | Berry bush clusters (verify exact `Objects` dataset name — likely `BERRY_BUSH` variants) with density + clumping |
| `FaunaScatterTemplate` | Generic animal scatter: pick species (deer, boar, sheep, wolves, bears, rabbits), herd size, density, clumping. Reused *inside* biomes too (replaces hardcoded fauna in nature.py) |
| `SnowyMountainRangeTemplate` | Perlin elevation ridge + snow terrain bands + snow pines + rocks + arctic fauna; parameters: ridge orientation, peak height, forest density |
| `LushForestTemplate` | Oak + pine mix, berry bushes, deer/boar herds, optional pond; the "green forest" preset |

### Layer 2 — Variety knobs on existing templates

- **City styles**: new `style` kwarg on `CityTemplate` — `trading` (marketplace,
  warehouses, more TCs), `military` (barracks, stables, extra towers),
  `religious` (cathedral, monastery), `port` (docks, fishing huts, water edge
  detection). Built from the existing district/prefab system
  (`city_district_templates.py`, `city_prefabs.py`) — mostly new prefab
  definitions + layout weights, not new machinery.
- **Village variants**: `variant` kwarg — `farming` (default), `fishing`
  (water edge, fishing huts, boats), `nomad` (tents instead of buildings,
  horses, no walls). Plus `size` tier (small/medium/large).
- **Fortress tier**: `tier` kwarg on `FortTemplate` — `outpost` (current),
  `fortress` (outer bailey wall + inner keep, moat option, double gate).

### Layer 3 — Composition ("recipes")

A thin `MapRecipe` layer above templates: a declarative spec that composes
terrain + settlements + resources + fauna in one call.

```python
recipe = MapRecipe(
    size=160,
    seed=42,
    terrain="snowy_mountains",          # or "lush_forest", "desert", custom PerlinTerrainConfig
    settlements=[
        Settlement("city", player=1, style="trading", at="corner"),
        Settlement("village", player=2, variant="fishing", at="water_edge"),
        Settlement("bandit_camp", at="forest", count=2),
    ],
    resources={"berries": 3, "gold_mines": 2, "stone_mines": 2},
    fauna={"deer": 4, "boar": 2},
)
mg = recipe.build()   # returns configured MapManager
mg.write_map_and_save("my_map.aoe2scenario")
```

Placement helpers (`at="corner" | "center" | "water_edge" | "forest" |
"random"`) resolve positions against the generated terrain so settlements land
on sensible tiles. This is the "quick and easy" layer — one call, interesting
result, deterministic per seed.

### Layer 4 — Frontend exposure (GeneralWebsite)

- New templates appear automatically in the Templates tab once registered
  (template list is driven by the backend `load-functions`/`apply-template`
  endpoints).
- New **"Quick Start" panel**: pick a recipe preset (Snowy Mountains +
  Trading City, Lush Forest + Bandit Camps, Desert + Oasis Villages, …),
  hit Generate, get a full map. Seed input + "reroll" button.
- Variety knobs (city style, village variant, fort tier) surface as dropdowns
  in the existing `ApplyTemplatePanel`.

## Phasing

| Phase | Deliverable | Effort |
|---|---|---|
| 1 | `FaunaScatterTemplate` + `BerryBushTemplate` (primitives, unblock everything else) | S |
| 2 | `BanditCampTemplate` | S–M |
| 3 | `SnowyMountainRangeTemplate` + `LushForestTemplate` | M |
| 4 | Variety knobs: city styles, village variants, fort tier | M |
| 5 | `MapRecipe` composition layer + 3–4 built-in presets | M |
| 6 | Frontend Quick Start panel + knob dropdowns | M |

Phases 1–3 are independent and can be parallelized. Phase 5 depends on 1–4.
Phase 6 depends on 5 (and on the backend exposing new templates).

## Validation Loop (per phase)

1. **Unit tests** in `src/aoe2mapgenerator/unit_tests/` — each template gets a
   test that builds a small map, applies the template, and asserts object
   counts / layer contents (pattern: `nature_template_test.py`).
2. **Example script** in `examples/` per new template (pattern:
   `city_example.py`) — writes a `.aoe2scenario` to `/tmp/`.
3. **Full suite**: `./run_tests.sh` (poetry install + pytest).
4. **Visual check**: `MapManager.visualize_map()` PNG, or load the scenario in
   AoE2 DE.
5. **Frontend** (phase 6): `npm run dev:all`, generate via Quick Start,
   verify in the canvas + in-game.

## Open Questions (need your input)

1. **Priorities** — which of the 6 phases matters most to you first? My
   suggested order is 1 → 2 → 3 (content first), but if you want the
   one-click experience sooner, we can do 1 → 5 → 6 and add content after.
2. **Bandit camp triggers** — should bandit camps ship with ambush triggers
   (bandits attack on approach), or be purely decorative units? Triggers add
   real gameplay value but more complexity.
3. **City style scope** — all four styles (trading/military/religious/port) or
   start with two?
4. **Recipe placement intelligence** — how smart should `at="water_edge"` etc.
   be? Simple (nearest matching tile) vs. smart (pathing/spacing checks so
   settlements don't overlap)?
5. **Berry dataset names** — need to verify exact `Objects` enum names in
   AoE2ScenarioParser 0.1.56 before implementing (will do in phase 1).
