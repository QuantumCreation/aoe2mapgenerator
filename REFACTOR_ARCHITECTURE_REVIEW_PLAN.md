# Refactor / Architecture Review Plan

## Scope

This document captures:

- a review of the current template handling architecture
- a repo-wide code review (correctness risks, architectural risks, maintainability issues)
- a refactor plan for performance, clarity, and modularity

No source code changes were made as part of this review.

## What I Reviewed

- `src/aoe2mapgenerator/templates/*` (including new city pipeline modules)
- `src/aoe2mapgenerator/map/*`
- `src/aoe2mapgenerator/units/placers/*`
- `src/aoe2mapgenerator/units/wallgenerators/*`
- `src/aoe2mapgenerator/serializer/*`
- `src/aoe2mapgenerator/scenario/*`
- `src/aoe2mapgenerator/triggers/*`
- `src/aoe2mapgenerator/visualizer/*`
- `src/aoe2mapgenerator/common/*`
- test suite layout and test behavior in `src/aoe2mapgenerator/unit_tests/*`
- top-level docs and scripts (`README.md`, `ARCHITECTURE.md`, `ARCHITECTURE.MD`, `run_tests.sh`)

## Validation Performed

- `pytest -q` from repo root
  - Failed during collection because Python imported an older installed package from `site-packages` instead of this repo's `src/` tree.
- `PYTHONPATH=src pytest -q`
  - Passed: `74 passed` (with 2 pytest mark warnings).

I also ran small local sanity checks to confirm a few latent bugs (not covered by tests), including template registration overwrite behavior, terrain point selection, serialization manager deserialization, and point-distance filtering behavior.

## Executive Summary

The project has a strong core idea and meaningful recent improvements (especially the newer city template pipeline), but the template system is currently in a transitional state with hidden global behavior and duplicate registrations. The biggest future payoff is to formalize templates as explicit, typed modules with a deterministic registry/bootstrap path and a clear plan/execution contract.

The codebase is functional (tests pass when run correctly), but there are several latent correctness bugs and architectural coupling points that will make future changes risky if left as-is.

## Template Handling Review (Current State)

## What exists today

- Template registration is global and side-effect based via `@register_template(...)` into a singleton registry in `src/aoe2mapgenerator/templates/template_decorator.py:8`.
- The registry silently overwrites an existing template for the same `TemplateType` in `src/aoe2mapgenerator/templates/templates_manager.py:44`.
- Template discovery occurs by importing modules purely for side effects in:
  - `src/aoe2mapgenerator/templates/__init__.py:11`
  - `src/aoe2mapgenerator/map/map_manager.py:31`
- Template invocation is mostly free-form `**kwargs` through `TemplateManager.apply_template(...)` in `src/aoe2mapgenerator/templates/templates_manager.py:46`.
- `TemplateConfig` is a generic wrapper with a small shared field set in `src/aoe2mapgenerator/templates/templates_manager.py:17`, but templates still depend heavily on ad-hoc kwargs.

## Main problems with the current template model

### 1) Duplicate registration for `TemplateType.CITY` (high risk)

Both files register `TemplateType.CITY`:

- `src/aoe2mapgenerator/templates/city_hybrid.py:691`
- `src/aoe2mapgenerator/templates/city.py:458`

Because the registry silently overwrites keys (`src/aoe2mapgenerator/templates/templates_manager.py:44`), whichever module imports last wins. This is global process state, so behavior can change based on import order, including third-party or notebook imports.

This is the most important template-system issue.

### 2) Side-effect imports hide system state and make startup behavior implicit

Template availability depends on import timing/order, not explicit initialization:

- `src/aoe2mapgenerator/templates/__init__.py:11`
- `src/aoe2mapgenerator/map/map_manager.py:31`

This makes the system difficult to reason about and difficult to test in isolation.

### 3) Template API contract is too loose (`**kwargs` everywhere)

`TemplateManager.apply_template(...)` composes a small shared config and forwards arbitrary kwargs (`src/aoe2mapgenerator/templates/templates_manager.py:67`). Templates then parse their own kwargs manually.

This creates:

- weak validation
- poor discoverability for UI/API integration
- drift between templates
- hidden backward-compat behavior (especially in city templates)

### 4) `TemplateConfig` duplicates the `point_collection` argument and is partially ignored

`TemplateConfig` includes `point_collection` (`src/aoe2mapgenerator/templates/templates_manager.py:20`), but `TemplateManager.apply_template(...)` does not read it and still requires a separate positional `point_collection` (`src/aoe2mapgenerator/templates/templates_manager.py:48`).

This creates two sources of truth.

### 5) Template abstraction does not match how templates are actually used

`AbstractTemplate` defines an abstract `__init__` and static `generate(...)` (`src/aoe2mapgenerator/templates/abstract_template.py:19`), but templates are effectively classes-as-namespaces with static methods, not instances.

This increases ceremony without enforcing a meaningful contract.

### 6) Legacy/unused template scaffolding creates confusion

- `src/aoe2mapgenerator/templates/template_holder.py:23` contains unimplemented `pass` methods.
- `src/aoe2mapgenerator/units/placers/statictemplate.py:8` is a stub class.

These look like an alternative template system that is no longer active.

## Recommended Future Template Architecture (Cleaner Approach)

## Target model

Adopt an explicit template platform with three layers:

1. `TemplateSpec` (metadata + typed params schema)
2. `TemplatePlanner` (optional, deterministic layout planning)
3. `TemplateExecutor` (applies placements to the map)

## Recommended design

### A) Explicit registry bootstrap (no side-effect imports)

Introduce a single startup function, e.g. `register_builtin_templates()`, that registers all built-in templates once.

Benefits:

- deterministic startup behavior
- easier tests
- no hidden import order bugs
- easier plugin/extension support

### B) Collision-safe registration

Make duplicate registration an error by default.

Allow explicit replacement only with an override flag, e.g. `replace=True`, and log it.

This would immediately surface the current `CITY` conflict.

### C) Typed parameter models per template (Pydantic/dataclass)

Instead of free-form kwargs, define per-template params:

- `FortTemplateParams`
- `CityTemplateParams`
- `PondTemplateParams`
- etc.

Registry stores the schema so callers/UI can introspect supported parameters.

Benefits:

- validation
- editor/type support
- clearer public API
- less template-specific parsing logic spread everywhere

### D) Versioned/aliased template IDs

Current conflict suggests a real product need: legacy city vs hybrid city.

Use explicit IDs, e.g.:

- `city.legacy`
- `city.hybrid`

and optionally map `TemplateType.CITY` to a default alias in one place.

### E) Standard template result object

Return a typed `TemplateResult` instead of inconsistent patterns (`self` vs `PointCollection` vs no return from manager dispatch). Include:

- placed/consumed points
- reserved masks (optional)
- metadata (e.g. gate positions, trigger areas)
- warnings/validation notes

This is especially useful for city templates and UI integrations.

### F) Separate planning from execution for complex templates

The new city hybrid pipeline already trends in this direction. Standardize it:

- plan objects are pure/deterministic and testable
- executor mutates `MapManager`

This is the right architecture for future large templates.

## Repo-Wide Code Review Findings

Findings are prioritized by impact.

## High Severity (correctness / unpredictable behavior)

### 1) `CITY` template registration is non-deterministic due to duplicate registration + silent overwrite

- `src/aoe2mapgenerator/templates/city_hybrid.py:691`
- `src/aoe2mapgenerator/templates/city.py:458`
- `src/aoe2mapgenerator/templates/templates_manager.py:44`
- `src/aoe2mapgenerator/templates/template_decorator.py:21`

Impact:

- `TemplateType.CITY` can resolve to different implementations depending on import order.
- Runtime behavior can drift in notebooks, tests, API workers, or future code paths.

Recommendation:

- Make duplicate registration an error.
- Introduce versioned template IDs / aliases.

### 2) `SerializationManager.deserialize()` is broken for serialized strings (latent bug)

- `src/aoe2mapgenerator/serializer/serialization_manager.py:52`
- `src/aoe2mapgenerator/serializer/base_serializer.py:67`

`SerializationManager.deserialize()` forwards `str | dict` directly into `SerializationRegistry.deserialize(...)`, but the registry expects a dict with `"_type"`. Passing a serialized string crashes.

Impact:

- Public serialization API is internally inconsistent.
- Likely to fail in integration code paths outside current tests.

Recommendation:

- Parse strings before registry dispatch.
- Add round-trip tests through `SerializationManager`, not just object methods.

### 3) `PointManager.get_collection_from_terrain()` is effectively unusable as written

- `src/aoe2mapgenerator/units/placers/point_management/point_manager.py:367`
- `src/aoe2mapgenerator/units/placers/point_management/point_manager.py:375`
- `src/aoe2mapgenerator/units/placers/placer_configs.py:132`
- `src/aoe2mapgenerator/units/placers/point_management/point_selector.py:37`

Problems:

- It passes a `TerrainId` where `PointSelectorConfig.object_type` is typed as `MapObject`.
- `PointSelector` does exact `MapObject` lookup, so terrain matches return empty in practice.
- Occupancy filtering checks `if not MapObject(...)`, but `MapObject` instances are truthy, so `exclude_occupied=True` filters out everything.

Impact:

- Terrain-derived point collection helper silently returns empty results.
- Callers will build workarounds instead of using the API.

Recommendation:

- Use `MapObject(terrain_type, PlayerId.GAIA)` for terrain lookups.
- Compare against `DEFAULT_EMPTY_OBJECT` (or equivalent helper) for occupancy.
- Add tests for this method specifically.

### 4) Point distance filtering is mathematically incorrect and asymmetric

- `src/aoe2mapgenerator/units/placers/point_management/point_collection.py:171`
- `src/aoe2mapgenerator/units/placers/point_management/point_collection.py:310`

`_get_points_within_distance()` uses `if i + j <= distance`, which is not Euclidean or Manhattan distance and is asymmetric (e.g. includes `(1, -1)` but excludes `(-1, 1)` in some cases).

Impact:

- Affects `get_nearby_points()` and `filter_by_distance()`.
- Can distort placement distributions and circular masks.

Recommendation:

- Use squared Euclidean or Manhattan consistently.
- Document which metric each API uses.

### 5) `Visualizer.visualize_map()` calls nonexistent methods on `Visualizer`

- `src/aoe2mapgenerator/visualizer/visualizer.py:163`

`self.get_map_layer(...)` is called, but `Visualizer` has no such method.

Impact:

- Method is broken if invoked.
- Indicates stale code path and insufficient coverage for visualizer helper APIs.

Recommendation:

- Fix or remove the method.
- Add a smoke test (optional dependency guarded) or clearly mark as internal/deprecated.

## Medium Severity (architecture / maintainability / performance risk)

### 6) `MapManager` eagerly loads the base scenario file on construction

- `src/aoe2mapgenerator/map/map_manager.py:76`
- `src/aoe2mapgenerator/scenario/scenario.py:57`

Every `MapManager(...)` instantiation parses a real `.aoe2scenario` file immediately, even for operations that never export.

Impact:

- startup latency
- filesystem/environment coupling
- harder testing in clean CI/containers

Recommendation:

- Lazily create/load `Scenario` only when `write_map_and_save()` (or trigger-related features) require it.

### 7) Template availability is managed via import side effects in multiple places

- `src/aoe2mapgenerator/templates/__init__.py:11`
- `src/aoe2mapgenerator/map/map_manager.py:31`

Impact:

- hidden global state
- accidental duplicate imports/registrations
- hard-to-test initialization order

Recommendation:

- centralize registration bootstrap and call it explicitly once.

### 8) `TemplateConfig` / `apply_template()` API has two sources of truth for the same input

- `src/aoe2mapgenerator/templates/templates_manager.py:20`
- `src/aoe2mapgenerator/templates/templates_manager.py:46`
- `src/aoe2mapgenerator/map/map_manager.py:294`

`point_collection` is both a positional argument and a field in `TemplateConfig`.

Impact:

- confusing call sites
- easy drift bugs if values diverge

Recommendation:

- Move to one typed params object plus explicit `selection`/`context`, or remove `point_collection` from `TemplateConfig`.

### 9) `AbstractTemplate` abstraction adds ceremony but not safety

- `src/aoe2mapgenerator/templates/abstract_template.py:19`

Impact:

- abstract `__init__` is mostly unused
- static `generate()` with `**kwargs` is not truly constrained

Recommendation:

- Replace with a Protocol or dataclass-based spec + callable executor contract.

### 10) Path-generation logic is duplicated (and behavior diverges)

- `src/aoe2mapgenerator/units/placers/path_placer.py:44`
- `src/aoe2mapgenerator/units/utils.py:39`

`PathPlacer` duplicates logic from `units/utils.py`. `PathPlacer` also deduplicates with `set()` (`src/aoe2mapgenerator/units/placers/path_placer.py:70`), which discards order.

Impact:

- bug fixes must be applied twice
- path order/reproducibility may differ unexpectedly

Recommendation:

- Consolidate into one path-generation module with ordered dedupe if needed.

### 11) Hardcoded machine/user filesystem paths in constants reduce portability

- `src/aoe2mapgenerator/common/constants/constants.py:12`
- `src/aoe2mapgenerator/common/constants/constants.py:20`
- `src/aoe2mapgenerator/map/map_manager.py:71`

Impact:

- environment-specific failures
- accidental writes to local machine paths
- difficult packaging/server deployment

Recommendation:

- Use environment variables / config objects.
- Make export path explicit at runtime.

### 12) Dead/stub modules increase conceptual load

- `src/aoe2mapgenerator/templates/template_holder.py:23`
- `src/aoe2mapgenerator/units/placers/statictemplate.py:8`

Impact:

- new contributors may follow obsolete patterns
- documentation drift risk

Recommendation:

- remove or clearly deprecate/document as legacy.

### 13) Serialization modules use broad exceptions and wildcard imports

- `src/aoe2mapgenerator/serializer/base_serializer.py:8`
- `src/aoe2mapgenerator/serializer/base_serializer.py:49`
- `src/aoe2mapgenerator/serializer/serialization_utils.py:2`
- `src/aoe2mapgenerator/serializer/serialization_utils.py:20`

Impact:

- masks real errors
- hard to reason about valid/invalid payload handling

Recommendation:

- replace broad `except:` with specific exceptions
- remove wildcard imports and duplicate imports

### 14) Test execution is easy to run against the wrong package

- `run_tests.sh:3`
- `README.md` test instructions imply Poetry paths but no `pytest` config ensures local `src/` import

Observed:

- plain `pytest -q` imported `site-packages/aoe2mapgenerator` first on this machine.

Recommendation:

- add pytest config (`pythonpath = ["src"]`) or enforce `poetry run pytest` consistently in docs/scripts.

### 15) Duplicate architecture docs likely to drift

- `ARCHITECTURE.md`
- `ARCHITECTURE.MD`

Impact:

- inconsistent guidance over time

Recommendation:

- keep one canonical file and delete/archive the duplicate.

## Low Severity / Cleanup Opportunities

### 16) Mutable default argument in `PointManager.add_point_collection(...)`

- `src/aoe2mapgenerator/units/placers/point_management/point_manager.py:38`

Current use may not mutate the default list directly, but it is still a known Python footgun.

### 17) `PointCollection.get_maximal_points()` returns topmost twice

- `src/aoe2mapgenerator/units/placers/point_management/point_collection.py:242`

Likely intended to return bottommost for the fourth element.

### 18) `Scenario.save_file()` prints directly to stdout

- `src/aoe2mapgenerator/scenario/scenario.py:96`

Library code should prefer structured logging or return the saved path.

### 19) `TemplateType` enum includes unimplemented/unused values

- `src/aoe2mapgenerator/templates/template_types.py:9`

This is not inherently wrong, but it makes the template surface area look larger than what is actually supported.

## Performance Refactor Opportunities

These are the highest-return performance improvements for future work.

## Priority A (high impact)

### 1) Lazy scenario loading

Problem:

- `MapManager` loads/parses a scenario file during construction.

Plan:

- initialize `self.scenario` lazily
- create/load only on export or trigger application
- support optional `scenario_factory` injection for tests

Expected benefit:

- lower object creation cost
- less filesystem coupling
- faster tests and API requests that only mutate maps

### 2) Reduce repeated `PointCollection.copy()` usage in templates

Files with heavy copy pressure:

- `src/aoe2mapgenerator/templates/nature.py`
- `src/aoe2mapgenerator/templates/city_hybrid.py`
- `src/aoe2mapgenerator/templates/city.py`

Plan:

- establish immutable source masks plus derived working masks
- cache `set(point_collection.get_point_list())` once when repeatedly queried
- use explicit "consumable" vs "read-only" collections

Expected benefit:

- lower memory churn
- improved large-map generation speed

### 3) Optimize `PointCollection` set/list operations

Problem examples:

- `intersect(..., edit_in_place=True)` uses repeated list membership checks (`src/aoe2mapgenerator/units/placers/point_management/point_collection.py:99`)

Plan:

- use dict-backed membership from the other collection
- avoid repeated `get_point_list()` calls inside loops
- define fast set-based variants for hot paths

Expected benefit:

- faster wall/city/template geometry operations

## Priority B (targeted improvements)

### 4) Consolidate path generation implementation

- Remove duplicate logic between `PathPlacer` and `units/utils.py`.
- Preserve order deterministically after dedupe (if dedupe is needed at all).

### 5) Visualizer large-map performance

- avoid full deep copies when not necessary
- optionally disable gridlines by default for large maps
- use vectorized remapping where possible

### 6) Serialization throughput

- reduce repeated per-cell object conversions during full-map serialization
- consider delta-based API responses for incremental operations

## Clarity / Modularity Refactor Plan

## Architectural Goals

- explicit initialization and registration
- typed boundaries between planning and map mutation
- fewer hidden globals
- clearer ownership of geometry, placement, and orchestration concerns
- stable public API surface with internal modules free to evolve

## Phased Refactor Plan (Recommended)

## Phase 0: Safety Net and Baseline (short)

Goals:

- lock in behavior before refactoring

Tasks:

- add tests for template registry collision behavior
- add tests for `PointManager.get_collection_from_terrain()`
- add tests for `PointCollection.filter_by_distance()` geometry
- add tests for `SerializationManager.deserialize()` round-trip
- add a smoke test for `Visualizer.visualize_map()` or mark/deprecate it

Success criteria:

- latent bugs reproduced by tests before fixes

## Phase 1: Template System Stabilization (highest priority)

Goals:

- make template selection deterministic and explicit

Tasks:

- introduce `TemplateRegistry` with collision policy (`error` on duplicate by default)
- create explicit bootstrap function for built-in template registration
- remove side-effect registration imports from `MapManager`
- choose one canonical `CITY` default and register the other under an alias/version
- deprecate/remove dead `TemplateHolder` and `TemplateCreator` scaffolding

Success criteria:

- `TemplateType.CITY` resolution is deterministic
- template availability no longer depends on incidental imports

## Phase 2: Typed Template Parameters + Introspection

Goals:

- replace free-form kwargs with validated, discoverable schemas

Tasks:

- define typed params models per template
- store schema metadata in registry
- migrate `TemplateManager.apply_template()` to accept typed params (with temporary compatibility wrapper)
- generate UI/API-friendly template parameter descriptions from schema metadata

Success criteria:

- invalid template params fail early with actionable errors
- callers can inspect supported params programmatically

## Phase 3: City Template Consolidation

Goals:

- treat legacy and hybrid city generators as deliberate versions, not collisions

Tasks:

- factor shared city concepts into common modules (presets, RNG policy, gate metadata)
- standardize `CityTemplate` planning/execution interfaces
- keep legacy implementation only if needed; otherwise migrate and retire
- add benchmark fixtures for city generation on representative map sizes

Success criteria:

- no duplicate registration
- shared city logic lives in explicit common modules
- clear migration path for callers

## Phase 4: Core Infrastructure Cleanup (map/points/serialization)

Goals:

- improve correctness and reduce hidden pitfalls

Tasks:

- fix `PointCollection` distance methods and document metric semantics
- fix terrain collection helper and occupancy filtering
- fix `SerializationManager.deserialize()`
- remove broad exception handling in serialization helpers
- eliminate mutable defaults and dead code paths
- normalize import style and remove wildcard imports in core infrastructure modules

Success criteria:

- targeted correctness bugs fixed and covered by tests
- core utilities easier to reason about

## Phase 5: Performance Pass

Goals:

- improve generation throughput and reduce startup overhead

Tasks:

- lazy scenario loading in `MapManager`
- profile nature/city templates on large maps (copy counts, hotspots)
- optimize repeated point-mask conversions and intersections
- reduce unnecessary deep copies in visualizer

Success criteria:

- measured improvements on representative scenarios
- no regressions in template outputs (or acceptable documented differences)

## Suggested Module Boundaries (Future State)

## `templates/` layout (proposed)

- `templates/registry.py` (registry + bootstrap)
- `templates/specs.py` (template metadata and IDs)
- `templates/params/` (typed params models)
- `templates/executors/` (actual template execution code)
- `templates/planners/` (complex layout planners, especially city)
- `templates/results.py` (`TemplateResult`)
- `templates/compat.py` (legacy kwargs adapter during migration)

## `geometry/` and `spatial/` utilities (proposed)

Extract reusable math/point-mask logic currently spread across:

- `PointCollection`
- `city_geometry.py`
- `units/utils.py`
- some placers

Use one shared, tested utility layer for:

- distance metrics
- line/path rasterization
- mask boolean ops
- neighborhood queries

## Risks During Refactor

- Output drift in procedural generation due to RNG order changes.
- Backward-compat breaks in external callers relying on current kwargs.
- Hidden notebook/import-order dependencies surfacing after registry cleanup.

Mitigations:

- add deterministic seed-based regression tests for key templates
- provide compatibility adapter layer for one release cycle
- introduce deprecation warnings before removing legacy paths

## Recommended Immediate Next Steps (Order)

1. Add tests reproducing the confirmed latent bugs and template collision behavior.
2. Fix duplicate `CITY` registration strategy (collision guard + alias/versioning).
3. Fix terrain point selection helper and distance filtering correctness.
4. Fix `SerializationManager.deserialize()` and add round-trip coverage.
5. Implement explicit template bootstrap and remove side-effect imports from `MapManager`.

## Appendix: Notable Complexity Hotspots

Largest Python modules by line count (useful for targeting modularization first):

- `src/aoe2mapgenerator/templates/nature.py`
- `src/aoe2mapgenerator/templates/city_hybrid.py`
- `src/aoe2mapgenerator/units/wallgenerators/fort_shapes.py`
- `src/aoe2mapgenerator/map/map_manager.py`
- `src/aoe2mapgenerator/templates/city.py`
- `src/aoe2mapgenerator/templates/settlement_helpers.py`

These should be primary candidates for incremental extraction into smaller, role-specific modules.
