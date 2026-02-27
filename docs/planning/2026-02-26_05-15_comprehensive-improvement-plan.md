# aoe2mapgenerator — Comprehensive Improvement Plan

**Created:** 2026-02-26 05:15 UTC  
**Status:** `PLANNED`  
**Task Type:** Review  
**Author:** Planner Agent  

---

## ⚠️ Instructions for Future Agents

> This document is a living record. If you are an agent reading this file:
>
> - **DO NOT re-investigate** what is already documented here unless the status is `SUPERSEDED`
> - If you implement anything from this plan, update the `Status` field and append an `## Implementation Log` entry
> - If this plan is outdated or replaced, mark it `SUPERSEDED` and link to the new document
> - If you make code changes based on this document, **commit them** with a message referencing this file

---

## Summary

A full architecture review of `aoe2mapgenerator` covering performance, feature completeness,
code quality, testing, developer experience, and packaging. Performance findings are
already thoroughly documented in `2026-02-26_00-00_performance-improvement-plan.md` and
are summarized here for completeness. This document focuses on the **eight additional
improvement dimensions** beyond performance that are actionable next steps.

---

## Codebase Context

### Stack & Architecture

| Layer | Technology |
|---|---|
| Python | 3.10+ |
| Data models | Pydantic 2.x `BaseModel` + `@dataclass` |
| Numeric | NumPy 1.26, SciPy 1.15 |
| Serialization | `ujson` + custom `Serializable` helpers |
| Tests | `pytest` 8.3 — functional, no benchmarks |
| Build | Poetry 0.1.4 |
| Type checking | mypy 1.15 |

### Key Module Inventory

| Module | Status | Notes |
|---|---|---|
| `map/map_manager.py` | Stable (714 lines) | Façade; method-chaining API |
| `map/imap_manager.py` | Stable (261 lines) | Protocol contract for templates |
| `templates/` | Active, incomplete | 15 types declared; ~6 unimplemented |
| `terrain/terrain.py` | Functional | Pure-Python perf bottleneck |
| `triggers/triggers.py` | Minimal (380 lines) | Only 2 trigger patterns |
| `triggers/city_life.py` | Functional | City-specific triggers, not generalized |
| `Cpython/Csetup.py` | Dead code | Empty Cython stub, never implemented |
| `units/placers/statictemplate.py` | Unclear purpose | Should likely be removed or documented |
| `visualizer/visualizer.py` | Basic Matplotlib | No export, no interactivity |

---

## Improvement 1 — Performance (Existing Plan)

> **See:** `docs/planning/2026-02-26_00-00_performance-improvement-plan.md`

Nine hotspots already documented and prioritized. Summary of top 4:

1. Voronoi L1 loop → vectorise with `scipy.spatial.cKDTree` (**Critical**)
2. Poisson active-list O(n) `del` → swap-and-pop O(1) (**High**)
3. Pure-Python Perlin noise → NumPy meshgrid (**High**)
4. `ObjectInfo` enum-by-name lookups → `@functools.lru_cache` (**High**)

**Recommended first action:** Stand up `pytest-benchmark` suite, then implement fixes
in severity order.

---

## Improvement 2 — Feature Completeness: Unimplemented Templates

### Finding
The `TemplateType` enum declares 22 values. At least 6 have no corresponding
implementation class registered with `TemplateManager`:

| `TemplateType` | Status |
|---|---|
| `CASTLE` | ❌ Not implemented |
| `MOUNTAIN` | ❌ Not implemented |
| `RIVER` | ❌ Not implemented (RIVER_SEGMENT in nature.py is a sub-primitive) |
| `ROAD` | ❌ Not implemented |
| `MINE` | ❌ Not implemented |
| `WALLS` | ❌ Not implemented |
| `FORT`, `VILLAGE`, `CITY`, `PALACE` | ✅ Implemented |
| `OAK_FOREST`, `SNOW_FOREST` | ✅ Implemented |
| `POND`, `RIVER_SEGMENT`, `PINE_FOREST`, etc. | ✅ Implemented (nature.py) |

### Proposed Plan
For each missing type, add a new implementation module under `templates/` following the
`AbstractTemplate` pattern and register it with `@register_template`.

**Priority order (by gameplay utility):**
1. `WALLS` — standalone perimeter walls without a full fort; very composable
2. `ROAD` — road network between two points (wraps `PathPlacer`; mostly already built)
3. `MINE` — gold/stone mine cluster with surrounding terrain
4. `MOUNTAIN` — elevation + rocky terrain patch using Perlin elevation
5. `CASTLE` — fortified structure (extension of `FortTemplate` + keep building)
6. `RIVER` — full river from edge-to-edge using `RIVER_SEGMENT` + Perlin curves

**Estimated Effort:** S–M each

---

## Improvement 3 — Trigger System Expansion

### Finding
`TriggerManager` exposes only two methods:
- `create_objects_in_area`
- `teleport_object_to_point`

`city_life.py` adds patrol triggers and city effects directly but bypasses
`TriggerManager`, creating a growing pile of one-off trigger helpers outside the
centralized manager.

### Proposed Plan
Expand `TriggerManager` to cover common gameplay patterns:

| Trigger Category | Specific Triggers to Add |
|---|---|
| **Win/Loss conditions** | `set_player_wins`, `set_player_loses`, `timer_win` |
| **Resource management** | `set_starting_resources`, `give_resources_to_player` |
| **Unit behaviour** | `patrol_between_points`, `task_unit_to_attack_area`, `set_unit_stance` |
| **Diplomacy** | `set_allied`, `set_enemy`, `set_neutral` |
| **Map events** | `reveal_area_to_player`, `change_object_ownership`, `change_terrain` |
| **Fog of war** | `explore_area`, `unexplore_area` |

Refactor `city_life.py` to call `TriggerManager` instead of raw
`AoE2DEScenario.trigger_manager` calls. This makes trigger logic testable and reusable
across templates.

**Estimated Effort:** M

---

## Improvement 4 — Scenario / Player Configuration

### Finding
`MapManager` produces scenario files but provides no API for:
- Player names and civilizations
- Starting positions per player (crucial for multiplayer maps)
- Starting age / starting resources
- Diplomacy settings (who is allied/enemy by default)
- Map victory conditions

These are all accessible via `AoE2ScenarioParser` but are not surfaced in
`MapManager`.

### Proposed Plan
Add a `ScenarioConfig` dataclass and a `configure_scenario(config: ScenarioConfig)`
method on `MapManager`:

```python
@dataclass
class PlayerConfig:
    player_id: PlayerId
    name: str = ""
    civilization: int = 0          # AoE2ScenarioParser CivId
    starting_food: int = 200
    starting_wood: int = 200
    starting_gold: int = 100
    starting_stone: int = 200
    starting_age: int = 2           # Dark Age = 2

@dataclass
class ScenarioConfig:
    players: list[PlayerConfig] = field(default_factory=list)
    diplomacy: dict[tuple[PlayerId, PlayerId], str] = field(default_factory=dict)
    map_name: str = "Generated Map"
    instructions: str = ""
```

**Estimated Effort:** M

---

## Improvement 5 — Code Quality & Architecture

### Finding A — Dead Code (`Cpython/`)
`src/aoe2mapgenerator/Cpython/Csetup.py` is an empty Cython setup stub. It was never
implemented. It creates confusion about whether there is a compiled C extension.
- **Action:** Delete `Cpython/` or add a `README.md` inside it explaining it is reserved
  for future C extension work.

### Finding B — `statictemplate.py` in `units/placers/`
`units/placers/statictemplate.py` does not belong with the placers. Its purpose is not
clear from the module name or location.
- **Action:** Investigate, relocate to `templates/` or remove.

### Finding C — Fragile `load_map()` rewiring
`MapManager.load_map()` manually reassigns `map` on 9 internal objects:
```python
self._base_placer.map = map_obj
self._wall_placer.map = map_obj
# ... 7 more ...
```
If a new collaborator is added to `__init__`, it is easy to forget to rewire it in
`load_map()`, causing subtle bugs.
- **Action:** Introduce a `_rewire_map(map_obj)` helper that iterates a registered list
  of collaborators, or give each collaborator a `bind_map(map: Map)` method and call it
  uniformly.

### Finding D — Inconsistent Config Strategy
`PlaceGroupsConfig`, `AddBordersConfig`, etc. are plain `@dataclass` with no validation.
`PerlinTerrainConfig` uses `@dataclass(frozen=True, slots=True)` with `__post_init__`
validation. `TemplateConfig` in `templates_manager.py` is yet another plain dataclass.
- **Action:** Standardize all config classes to use `@dataclass(frozen=True)` with
  `__post_init__` validation guards (e.g., `groups >= 1`, `0.0 <= group_density <= 1.0`).
  This catches misuse at config construction time rather than deep inside placement logic.

### Finding E — `AbstractTemplate.generate()` lacks type safety
The signature is:
```python
@staticmethod
@abstractmethod
def generate(map_manager, point_collection, player_id=..., **kwargs) -> PointCollection:
```
All template-specific parameters are swallowed by `**kwargs`. This means callers get no
IDE autocompletion and type checkers cannot verify arguments.
- **Action:** Add a `Config` inner dataclass to each template class and change the
  signature to `generate(map_manager, config: T)` where `T` is the template-specific
  config type. The generic `TemplateConfig` in `templates_manager.py` can remain as a
  common denominator for the registry API, with templates narrowing on construction.

### Finding F — `MapManager` is 714 lines
Much of this is boilerplate delegation. Consider extracting:
- **`ScenarioMixin`** — `write_map_and_save`, `configure_scenario`
- **`TemplateMixin`** — `apply_template`, `apply_templates`
- **`VisualizationMixin`** — `visualize_map`

**Estimated Effort per finding:** XS–S

---

## Improvement 6 — Testing & CI

### Finding A — No Performance Benchmarks
The performance planning doc proposes `pytest-benchmark` but it is not yet in
`pyproject.toml` and no benchmark tests exist.
- **Action:** See `2026-02-26_00-00_performance-improvement-plan.md` — Performance Test
  Plan section for the full test file set.

### Finding B — No CI Pipeline
There is no `.github/workflows/` directory. Tests can only be run manually.
- **Action:** Add a GitHub Actions workflow:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install poetry && poetry install
      - run: poetry run pytest src/aoe2mapgenerator/unit_tests -q
      - run: poetry run mypy src
```

### Finding C — No Property-Based Tests
`PointCollection`, `MapLayer`, and `Serializable` are all good candidates for
[Hypothesis](https://hypothesis.readthedocs.io/) property-based tests (e.g., "adding
then removing a point always leaves the collection unchanged").
- **Action:** Add `hypothesis` to dev dependencies; add at minimum 3 property tests
  for `PointCollection` and `MapLayer`.

### Finding D — No End-to-End Scenario File Test
Existing tests stop at the `MapManager` level; no test exercises the full
`write_map_and_save()` → `.aoe2scenario` file pipeline.
- **Action:** Add one integration test that generates a small map (size=20),
  writes it to a temp file, then re-parses it with `AoE2ScenarioParser` and checks
  a few expected properties.

**Estimated Effort:** M total for B + C + D

---

## Improvement 7 — Developer Experience & API

### Finding A — No Seed-Based Deterministic Mode
Maps are generated with various `random.Random` instances. There is no single top-level
`seed` parameter on `MapManager` that pins all randomness.
- **Action:** Add `seed: int | None = None` to `MapManager.__init__`. Seed a shared
  `random.Random` instance and pass it down to `VoronoiGenerator`, `PerlinTerrainGenerator`,
  and any template that uses `random.*`. This enables reproducible map sharing by sharing
  the seed value.

### Finding B — Cross-Platform Output Path
`BASE_SCENE_DIR_WINDOWS_WSL` in `constants.py` is the default `output_dir` for
`MapManager` and is hardcoded to a WSL/Windows path. This makes the library only
usable out-of-the-box on that specific machine.
- **Action:** Change the default to:
  ```python
  import tempfile, os
  DEFAULT_OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "aoe2mapgenerator_output")
  ```
  and document that users should override `output_dir` to their AoE2 scenario folder.

### Finding C — No High-Level Workflow Helpers
New users must manually create `PointCollection`, fill it with all tiles, then pass it
to every operation. This is boilerplate that should be hidden.
- **Action:** Add convenience methods to `MapManager`:
  - `mm.all_points()` → `PointCollection` of every tile
  - `mm.points_in_rect(x1, y1, x2, y2)` → `PointCollection`
  - `mm.points_from_zone(zone_obj: MapObject)` → `PointCollection` of tiles in that zone

### Finding D — Missing `__all__` Exports
`src/aoe2mapgenerator/__init__.py` does not export any symbols. Users must know the
internal module path to import anything.
- **Action:** Populate `__init__.py` with a clean public API surface:
  ```python
  from aoe2mapgenerator.map.map_manager import MapManager
  from aoe2mapgenerator.map.map import Map
  from aoe2mapgenerator.templates.template_types import TemplateType
  from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig, ...
  __all__ = ["MapManager", "Map", "TemplateType", ...]
  ```

**Estimated Effort:** S–M each

---

## Improvement 8 — Documentation & Examples

### Finding A — README is Minimal
`README.md` covers only installation and test invocation. It has no example code, no
map output screenshots, and no feature overview.
- **Action:** Add:
  - A "Quick Start" section with a 15-line end-to-end example
  - A feature table (templates, terrain generation, trigger system)
  - A screenshot or ASCII art of a sample generated map

### Finding B — No `examples/` Directory
`RoyalRoadScraper` (sibling project) has a well-organized `examples/` directory with
`basic_usage.py`, `django_integration.py`, etc. `aoe2mapgenerator` has none.
- **Action:** Add `examples/`:
  - `basic_map.py` — minimal MapManager + place_groups + write_map_and_save
  - `terrain_example.py` — Perlin terrain + elevation generation
  - `city_example.py` — apply city template
  - `nature_example.py` — pond + pine forest + savannah biome
  - `notebook_quickstart.ipynb` — interactive Jupyter demo with visualizer output

### Finding C — No API Reference
There is no generated API documentation (Sphinx, mkdocs, etc.).
- **Action:** Add `mkdocs` with `mkdocstrings` (or Sphinx):
  - Document all public classes with docstrings already present
  - Link from README to hosted docs (GitHub Pages)

**Estimated Effort:** M total

---

## Improvement 9 — Packaging & Distribution

### Finding A — Dev Tools in Production Dependencies
`mypy`, `pytest`, `ipykernel`, `pydeps` are in `[tool.poetry.dependencies]` instead
of `[tool.poetry.group.dev.dependencies]`. This bloats the installed package for
downstream users.
- **Action:** Move to `[tool.poetry.group.dev.dependencies]`:
  ```toml
  [tool.poetry.group.dev.dependencies]
  pytest = "^8.3"
  mypy = "^1.15"
  ipykernel = "^6.29"
  pydeps = "^3.0"
  pytest-benchmark = "^4.0"
  hypothesis = "^6.0"
  ```

### Finding B — Dual Egg-Info Directories
Both `aoe2_map_generator.egg-info/` and `aoe2mapgenerator.egg-info/` exist in the
source tree, suggesting the package was renamed at some point. Both directories should
be git-ignored and the stale one removed.
- **Action:** Add `*.egg-info/` to `.gitignore`; delete `aoe2_map_generator.egg-info/`.

### Finding C — No `__version__`
There is no `__version__` attribute exported from the package.
- **Action:** Add to `src/aoe2mapgenerator/__init__.py`:
  ```python
  __version__ = "0.1.4"
  ```
  Or use `importlib.metadata` to read from `pyproject.toml` at runtime.

### Finding D — No PyPI Publishing Workflow
- **Action:** Add a GitHub Actions workflow `publish.yml` triggered on tagged releases
  to publish to TestPyPI first, then PyPI.

**Estimated Effort:** XS–S each

---

## Priority Matrix

| # | Area | Impact | Effort | Priority |
|---|---|---|---|---|
| 1 | Performance (existing plan) | Critical | M | ⬆ Do now |
| 2 | Cross-platform output path | High | XS | ⬆ Do now |
| 2 | `MapManager.all_points()` helpers | High | XS | ⬆ Do now |
| 3 | `__all__` public API exports | Medium | XS | Soon |
| 4 | Seed-based determinism | High | S | Soon |
| 5 | Move dev deps to dev group | Medium | XS | Soon |
| 6 | CI GitHub Actions | Medium | S | Soon |
| 7 | Dead code removal (`Cpython/`, `statictemplate.py`) | Low | XS | Soon |
| 8 | Config validation guards | Medium | S | Next milestone |
| 9 | Expand TriggerManager | High | M | Next milestone |
| 10 | Missing templates (WALLS, ROAD, MINE, etc.) | High | M each | Next milestone |
| 11 | Scenario/Player configuration API | Medium | M | Next milestone |
| 12 | `load_map()` rewiring refactor | Medium | S | Next milestone |
| 13 | End-to-end integration test | Medium | S | Next milestone |
| 14 | Property-based tests (Hypothesis) | Medium | M | Next milestone |
| 15 | README + examples/ | Medium | M | Next milestone |
| 16 | Type-safe template configs | Medium | M | Future |
| 17 | MapManager decomposition (Mixins) | Low | L | Future |
| 18 | API docs (mkdocs/Sphinx) | Low | M | Future |
| 19 | Interactive visualizer (Jupyter widgets) | Low | M | Future |
| 20 | NumPy-backed MapLayer (Perf Finding 7) | Critical (long-term) | XL | Far future |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Template additions break existing template registry collision detection | Low | Medium | Existing `replace=False` guard will catch double-registrations; add tests |
| Seed propagation touches many random call sites, misses some | Medium | Low | Add a determinism test: generate same map twice with same seed, assert equality |
| Moving deps to dev group breaks downstream installs that relied on transitive deps | Low | Medium | Test with a fresh `pip install aoe2mapgenerator` after pyproject.toml update |
| CI on GitHub Actions fails due to AoE2ScenarioParser GitHub dependency | Medium | Medium | Ensure `pyproject.toml` pins a released version of AoE2ScenarioParser, not a git URL |
| `load_map()` refactor introduces rewiring regression | Low | High | Add dedicated `test_load_map_rewires_all_collaborators` test before refactor |

---

## Open Questions

- [ ] Should `MapManager` support rectangular (non-square) maps? Currently only `size: int` is accepted.
- [ ] Is PyPI publishing desired? The package currently has no public visibility beyond the GitHub repo.
- [ ] Which unimplemented templates should be prioritized — `WALLS`/`ROAD` (utility) or `CASTLE`/`MOUNTAIN` (aesthetics)?
- [ ] Should the `TriggerManager` cover all AoE2ScenarioParser trigger effects, or only a curated subset?
- [ ] Should `CITY` and other complex templates expose their district `PointCollection` results to callers so they can layer additional customization on top?

---

## Implementation Log

> Append entries here when this plan is acted upon. Do not edit prior entries.

<!-- Example entry:
### [YYYY-MM-DD HH:MM UTC] — [Agent or Human ID]
**Status Change:** PLANNED → IN PROGRESS
**What was done:** ...
**Commits:** `abc1234`
**Notes:** ...
-->
