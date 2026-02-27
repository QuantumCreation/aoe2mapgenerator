# aoe2mapgenerator — Performance Improvement Plan

**Created:** 2026-02-26 00:00 UTC  
**Status:** `PLANNED`  
**Task Type:** Performance  
**Author:** Planner Agent  

---

## ⚠️ Instructions for Future Agents

> This document is a living record. If you are an agent reading this file:
>
> - **DO NOT re-investigate** what is already documented here unless the status is `SUPERSEDED`
> - If you implement anything from this plan, update the `Status` field and append an `## Implementation Log` entry (see bottom of this file for format)
> - If this plan is outdated or replaced, mark it `SUPERSEDED` and link to the new document
> - If you make code changes based on this document, **commit them** with a message referencing this file

---

## Summary

The `aoe2mapgenerator` library generates AoE2 scenario maps procedurally. Performance
degrades non-linearly with map size because several core algorithms use Python-level
loops where NumPy/SciPy vectorisation is both straightforward and safe. Six specific
hotspots account for the majority of execution time; three of them can be resolved with
minimal API surface changes. A dedicated `tests/performance/` suite of `pytest-benchmark`
tests is proposed to measure all hotspots before and after each change.

---

## Codebase Context

### Stack & Architecture

| Layer | Technology |
|---|---|
| Python | 3.10+ |
| Data models | Pydantic 2.x `BaseModel` |
| Numeric | NumPy 1.26, SciPy 1.15 |
| Serialization | `ujson` + custom `Serializable` helpers |
| Tests | `pytest` 8.3 — functional only (no benchmarks yet) |
| Build | Poetry |

The library follows a Façade pattern (`MapManager`) over specialist helpers
(`GroupPlacer`, `VoronoiGenerator`, `PerlinTerrainGenerator`, etc.).  The central
data structure is `MapLayer`, which keeps a `list[list[MapObject]]` array **and** a
`dict[MapObject, set[Point]]` reverse index in sync via `set_point()`.

### Relevant Files & Modules

| File | Role |
|---|---|
| `map/maplayer.py` | Core grid + reverse-dict; `set_point()` is the single mutation path |
| `map/map_object.py` | `@dataclass(frozen=True)` value type; `__hash__` based on `(obj_type, player_id)` |
| `units/wallgenerators/voronoi.py` | `generate_voronoi_l1`, `_poisson_disk_sample` |
| `units/placers/group_placer.py` | `place_groups`, `_prepare_points_list`, `_place_objects` |
| `units/placers/placer_base.py` | `_place_single`, `_check_placement`, `fill` |
| `units/placers/point_management/point_collection.py` | `get_nearby_points` → `_get_points_within_distance` |
| `units/placers/object_info.py` | `ObjectInfo.get_object_*` static helpers |
| `terrain/terrain.py` | `generate_noise_matrix` (pure-Python nested loops) |

---

## Analysis Findings

### Finding 1 — O(seeds × grid²) Voronoi distance loop
- **Severity:** Critical
- **Details:**  
  `generate_voronoi_l1` (voronoi.py L307–345) iterates over every seed point and for
  each one computes a full `(rows, cols)` L1 distance array, then updates a running
  min via a boolean mask.  For 100 seeds on a 200×200 grid this creates **100 temporary
  NumPy arrays of shape (200,200)** and runs 100 boolean mask updates.  The correct
  approach is a single `scipy.spatial.cKDTree.query()` call with `p=1` (L1 norm), which
  computes all nearest-seed distances in one vectorised pass.
- **Location:** `src/aoe2mapgenerator/units/wallgenerators/voronoi.py:307`

### Finding 2 — O(n) `del` inside Poisson disk sampling hot loop  
- **Severity:** High
- **Details:**  
  `_poisson_disk_sample` (voronoi.py ~L258) removes a random element from the active
  list with `del points[index]`, which is O(n) because Python lists are contiguous
  arrays.  The fix is a one-liner: swap the chosen element with the tail and pop, making
  removal O(1):
  ```python
  # Before
  p = points[index]
  del points[index]
  # After
  points[index] = points[-1]
  p = points.pop()
  ```
- **Location:** `src/aoe2mapgenerator/units/wallgenerators/voronoi.py` (Bridson active-list loop)

### Finding 3 — Pure-Python Perlin noise generation
- **Severity:** High  
- **Details:**  
  `generate_noise_matrix` (terrain.py) uses two nested Python `for` loops — one per tile
  — each calling `_fractal_perlin_value` which itself loops `octaves` times.  For a
  200×200 map with 4 octaves this is **160,000 Python function calls** per invocation.
  Vectorising the entire noise field as a single NumPy operation would yield 50–200×
  speedup.  The deterministic seeded `_Perlin2D` class can be kept; only the outer
  iteration needs to move into NumPy.
- **Location:** `src/aoe2mapgenerator/terrain/terrain.py:generate_noise_matrix`

### Finding 4 — ObjectInfo Enum name lookup on every placement
- **Severity:** High
- **Details:**  
  `ObjectInfo.get_object_rows/columns/size/effective_size` each call
  `ObjectSize(aoe2_object._name_).value`, which reconstructs the Enum member by name
  string every call.  `_place_single` calls **5 of these methods per placed tile**, and
  `_check_placement` calls 4 more.  For 50,000 tile placements on a 200×200 map, this
  is **450,000+** Enum-by-name string lookups.  Decorating each method with
  `@functools.lru_cache(maxsize=None)` caps the cost at O(1) after the first lookup
  per `(obj_type, margin)` pair.
- **Location:** `src/aoe2mapgenerator/units/placers/object_info.py`

### Finding 5 — O((2d)²) spatial scan for `get_nearby_points`
- **Severity:** Medium
- **Details:**  
  `_get_points_within_distance(point, distance)` iterates over a `(2d+1)×(2d+1)`
  bounding square, doing one dict lookup per cell.  Called during every `_prepare_points_list`
  (once per group placement), with `distance = (total_size**0.5) * 2`.  For groups of
  size 25 with margin 1, `total_size ≈ 25`, `distance ≈ 10` → 441 dict lookups per
  group.  At 200 groups this is 88,200 lookups — acceptable, but approaches 40,000+
  lookups for larger groups.  A grid-hash spatial structure (bucket by cell) would make
  this O(result_count) instead of O(d²).
- **Location:** `src/aoe2mapgenerator/units/placers/point_management/point_collection.py:_get_points_within_distance`

### Finding 6 — Repeated O(n) bounding-box scans in PointCollection
- **Severity:** Medium  
- **Details:**  
  `get_x_point_range()` calls `get_topmost_point()` and `get_bottommost_point()`, each
  doing a full `min`/`max` scan over `__points_list` (O(n)).  Similarly for
  `get_y_point_range()`.  These are called once per `generate_voronoi_cells` invocation
  to determine the region dimensions.  They can be replaced with maintained `_min_x`,
  `_max_x`, `_min_y`, `_max_y` counters updated on every `add_point` / `remove_point`,
  making all four accessors O(1).  (Note: `remove_point` would need to re-scan on a
  boundary removal, but this is rare.)
- **Location:** `src/aoe2mapgenerator/units/placers/point_management/point_collection.py`

### Finding 7 — MapLayer backed by Python list-of-lists
- **Severity:** Medium (long-term)
- **Details:**  
  `MapLayer.array` is a `list[list[MapObject]]`.  Each cell is a Python object reference.
  For a 200×200 map this means 40,000 Python objects just for the default empty tiles.
  A NumPy int32 array encoding `(obj_type_id, player_id)` as a packed integer would
  reduce memory by ~8–12× and make bulk operations (filling, copying, serialising)
  significantly faster.  This is a large API change and should be done last.
- **Location:** `src/aoe2mapgenerator/map/maplayer.py`

### Finding 8 — `fill()` copies entire point list upfront
- **Severity:** Low
- **Details:**  
  `fill()` calls `get_point_list_copy()` before iterating, which copies the full list
  (up to 40,000 tuples) even when only a small fraction of tiles will be filled.  If
  `_check_placement` rarely succeeds (sparse fill), this is pure overhead.  Iterating
  over a copy is necessary to avoid mutation-during-iteration, but a snapshot of just
  the keys of `dictionary` might be more efficient since those already reflect the
  available set.
- **Location:** `src/aoe2mapgenerator/units/placers/placer_base.py:fill`

### Finding 9 — `_place_path` reuses `PlaceIfPossibleConfig` inside loop
- **Severity:** Low
- **Details:**  
  `_place_path` creates a new `PlaceIfPossibleConfig` dataclass instance for every point
  in the path list.  For long paths (1,000+ tiles) this instantiates 1,000+ Pydantic
  models just to pass immutable data through.  The config fields except `starting_point`
  are constant; a lighter approach would inline the placement check or reuse a mutable
  config struct.
- **Location:** `src/aoe2mapgenerator/units/placers/path_placer.py:_place_path`

---

## Proposed Plan

### Option A — Targeted hotspot fixes (RECOMMENDED)

Address the four highest-severity findings independently, in isolation, with a benchmark
gate on each.  No API breakage.  Each fix is a self-contained PR.

**Estimated Effort:** M (2–3 days per finding, total ~2 weeks)

**Steps:**

1. **Stand up benchmark suite** (prerequisite for all further work — see *Performance Test Plan* below)
2. **Fix Finding 2** — O(1) Poisson active-list removal  
   - 1-line change, immediate measurable speedup for large voronoi calls
3. **Fix Finding 4** — `@lru_cache` on all `ObjectInfo` static methods  
   - 3-line change, immediate speedup for every `place_groups` call
4. **Fix Finding 1** — Vectorise Voronoi with `cKDTree`  
   - Replace `generate_voronoi_l1` body with a `cKDTree.query` call; `scipy` is already a dep
5. **Fix Finding 3** — Vectorise Perlin noise  
   - Rewrite `generate_noise_matrix` to build coordinate meshgrid once, evaluate all octaves as NumPy broadcasts
6. **Fix Finding 6** — Cache bounding box in `PointCollection`  
   - Maintain 4 counters; invalidate on boundary removal; add `_rebuild_bounds()` fallback
7. **Fix Finding 5** — Grid-hash spatial index  
   - Add `_cell_size` parameter and `_grid: dict[tuple[int,int], list[Point]]` to `PointCollection`
8. (Future) **Fix Finding 7** — NumPy-backed `MapLayer`  
   - Major refactor; defer until benchmarks confirm it is still a bottleneck after above fixes

### Option B — NumPy-first rewrite

Replace `MapLayer` with a NumPy-backed store from the outset, rewriting all accessors.
Delivers maximum throughput but risks regressions in edge-case behaviour and requires
extensive test coverage before merging.

**Estimated Effort:** XL (3–4 weeks)  
**Tradeoffs:** Highest ceiling but breaks existing API contracts; should only be considered if benchmarks after Option A still show MapLayer I/O as dominant cost.

---

## Performance Test Plan

### Infrastructure

Install `pytest-benchmark` (not yet in `pyproject.toml`):

```toml
[tool.poetry.dev-dependencies]
pytest-benchmark = "^4.0"
```

Create a new directory `src/aoe2mapgenerator/unit_tests/performance/` with its own
`conftest.py`.  Tests use `benchmark()` fixtures provided by `pytest-benchmark`.

Run baseline **before** any code changes:

```bash
cd /home/joey/Documents/Projects/aoe2mapgenerator
poetry run pytest src/aoe2mapgenerator/unit_tests/performance/ \
  --benchmark-save=baseline \
  --benchmark-columns=min,mean,stddev,rounds
```

Re-run after each fix and compare:

```bash
poetry run pytest src/aoe2mapgenerator/unit_tests/performance/ \
  --benchmark-compare=baseline \
  --benchmark-compare-fail=mean:10%
```

---

### Test Files

#### `perf_voronoi.py` — Voronoi & Poisson sampling

```python
"""Benchmarks for VoronoiGenerator and the Poisson disk sampler."""
import pytest
import numpy as np
from aoe2mapgenerator.units.wallgenerators.voronoi import generate_voronoi_l1
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.placer_configs import VoronoiGeneratorConfig
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


@pytest.mark.parametrize("grid_size,n_seeds", [
    (100, 20),
    (200, 50),
    (400, 100),
])
def test_bench_generate_voronoi_l1(benchmark, grid_size, n_seeds):
    """Raw benchmark of the voronoi grid computation."""
    rng = np.random.default_rng(42)
    seeds = [(int(x), int(y))
             for x, y in rng.integers(0, grid_size, size=(n_seeds, 2))]

    benchmark(generate_voronoi_l1, grid_size, grid_size, seeds)


@pytest.mark.parametrize("n", [50, 100, 200])
def test_bench_full_voronoi_pipeline(benchmark, n):
    """End-to-end voronoi zone placement via MapManager."""
    def run():
        mm = MapManager(n)
        mm.point_manager.add_point_collection("pts")
        mm.point_manager.get_point_collection("pts").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )
        cfg = VoronoiGeneratorConfig(
            point_collection=mm.point_manager.get_point_collection("pts"),
            interpoint_distance=10,
            map_layer_type=MapLayerType.UNIT,
        )
        mm.place_voronoi_zones(cfg)

    benchmark(run)


@pytest.mark.parametrize("map_size,radius", [
    (100, 8),
    (200, 10),
    (400, 15),
])
def test_bench_poisson_disk_sample(benchmark, map_size, radius):
    """Benchmark the Poisson disk sampler at different scales."""
    from aoe2mapgenerator.units.wallgenerators.voronoi import VoronoiGenerator
    from aoe2mapgenerator.map.map import Map

    gen = VoronoiGenerator(Map(size=map_size))

    benchmark(gen._poisson_disk_sample, map_size, map_size, radius, 30)
```

---

#### `perf_group_placer.py` — Group placement pipeline

```python
"""Benchmarks for GroupPlacer and PlacerBase."""
import pytest
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


def _make_full_collection(n: int) -> PointCollection:
    pc = PointCollection()
    pc.add_points([(i, j) for i in range(n) for j in range(n)])
    return pc


@pytest.mark.parametrize("n,groups,group_size", [
    (100, 50, 10),
    (200, 200, 20),
    (200, 500, 5),
])
def test_bench_place_groups(benchmark, n, groups, group_size):
    """Benchmark place_groups at varying densities."""
    def run():
        mm = MapManager(n)
        mm.point_manager.add_point_collection("pts")
        mm.point_manager.get_point_collection("pts").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )
        cfg = PlaceGroupsConfig(
            object_type=UnitInfo.MILITIA,
            map_layer_type=MapLayerType.UNIT,
            point_collection=mm.point_manager.get_point_collection("pts"),
            groups=groups,
            group_size=group_size,
            player_id=PlayerId.ONE,
            margin=0,
            clumping=0,
        )
        mm.place_groups(cfg)

    benchmark(run)


@pytest.mark.parametrize("n", [100, 200])
def test_bench_fill(benchmark, n):
    """Benchmark fill() for an entire layer."""
    from aoe2mapgenerator.units.placers.placer_configs import FillConfig
    from AoE2ScenarioParser.datasets.terrains import TerrainId

    def run():
        mm = MapManager(n)
        mm.point_manager.add_point_collection("pts")
        mm.point_manager.get_point_collection("pts").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )
        cfg = FillConfig(
            object_type=TerrainId.GRASS_2,
            map_layer_type=MapLayerType.TERRAIN,
            point_collection=mm.point_manager.get_point_collection("pts"),
            player_id=PlayerId.GAIA,
            margin=0,
        )
        mm._base_placer.fill(cfg)

    benchmark(run)
```

---

#### `perf_terrain.py` — Perlin noise generation

```python
"""Benchmarks for PerlinTerrainGenerator."""
import pytest
from aoe2mapgenerator.terrain.terrain import PerlinTerrainGenerator, PerlinNoiseConfig
from aoe2mapgenerator.map.map import Map


@pytest.mark.parametrize("w,h", [
    (100, 100),
    (200, 200),
    (400, 400),
])
def test_bench_generate_noise_matrix(benchmark, w, h):
    """Benchmark noise matrix generation (pure Python inner loop)."""
    gen = PerlinTerrainGenerator(Map(size=max(w, h)))
    cfg = PerlinNoiseConfig(seed=0, scale=24.0, octaves=4)

    benchmark(gen.generate_noise_matrix, w, h, cfg)
```

---

#### `perf_maplayer.py` — MapLayer mutation throughput

```python
"""Benchmarks for MapLayer.set_point() throughput."""
import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.map.maplayer import MapLayer
from aoe2mapgenerator.common.enums.enum import MapLayerType


@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_set_point_sequential(benchmark, n):
    """Sequential set_point over entire layer."""
    layer = MapLayer(map_layer_type=MapLayerType.TERRAIN, size=n)

    def run():
        for i in range(n):
            for j in range(n):
                layer.set_point((i, j), TerrainId.GRASS_2, PlayerId.GAIA)

    benchmark(run)


@pytest.mark.parametrize("n", [100, 200])
def test_bench_maplayer_init(benchmark, n):
    """Benchmark MapLayer construction (initial list-of-lists + dict creation)."""
    benchmark(MapLayer, map_layer_type=MapLayerType.TERRAIN, size=n)
```

---

#### `perf_point_collection.py` — Spatial query performance

```python
"""Benchmarks for PointCollection spatial queries."""
import pytest
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection


def _make_collection(n: int) -> PointCollection:
    pc = PointCollection()
    pc.add_points([(i, j) for i in range(n) for j in range(n)])
    return pc


@pytest.mark.parametrize("n,distance", [
    (100, 5),
    (100, 20),
    (200, 5),
    (200, 20),
    (200, 50),
])
def test_bench_get_nearby_points(benchmark, n, distance):
    """Benchmark get_nearby_points at different search radii."""
    pc = _make_collection(n)
    center = (n // 2, n // 2)

    benchmark(pc.get_nearby_points, center, distance)


@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_get_x_point_range(benchmark, n):
    """Benchmark bounding-box computation (currently O(n) min/max scan)."""
    pc = _make_collection(n)

    benchmark(pc.get_x_point_range)


@pytest.mark.parametrize("n", [100, 200, 400])
def test_bench_add_remove_points(benchmark, n):
    """Benchmark a mixed add/remove sequence."""
    points = [(i, j) for i in range(n) for j in range(n)]

    def run():
        pc = PointCollection()
        pc.add_points(points)
        for p in points[:len(points) // 4]:
            pc.remove_point(p)

    benchmark(run)
```

---

#### `perf_object_info.py` — ObjectInfo cache effectiveness

```python
"""Benchmarks for ObjectInfo: measures Enum lookup cost."""
import pytest
from AoE2ScenarioParser.datasets.units import UnitInfo
from aoe2mapgenerator.units.placers.object_info import ObjectInfo


_SAMPLE_TYPES = [UnitInfo.MILITIA, UnitInfo.ARCHER, UnitInfo.KNIGHT,
                 UnitInfo.MANGUDAI, UnitInfo.TREBUCHET_PACKED]


@pytest.mark.parametrize("obj_type", _SAMPLE_TYPES)
def test_bench_object_info_get_size(benchmark, obj_type):
    """get_object_size lookup — should be O(1) with lru_cache."""
    benchmark(ObjectInfo.get_object_size, obj_type)


def test_bench_object_info_burst(benchmark):
    """Simulates 50,000 successive lookups as seen during place_groups."""
    def run():
        for _ in range(50_000):
            ObjectInfo.get_object_size(UnitInfo.MILITIA)

    benchmark(run)
```

---

#### `perf_full_map.py` — End-to-end generation

```python
"""End-to-end map generation benchmarks."""
import pytest
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.placer_configs import (
    VoronoiGeneratorConfig,
    PlaceGroupsConfig,
)


@pytest.mark.parametrize("n", [50, 100, 200])
def test_bench_full_map_generation(benchmark, n):
    """
    Realistic scenario: Voronoi zones + group placement across the full map.
    Serves as the top-level regression guard.
    """
    def run():
        mm = MapManager(n)
        mm.point_manager.add_point_collection("all")
        mm.point_manager.get_point_collection("all").add_points(
            [(i, j) for i in range(n) for j in range(n)]
        )

        vcfg = VoronoiGeneratorConfig(
            point_collection=mm.point_manager.get_point_collection("all"),
            interpoint_distance=max(5, n // 20),
            map_layer_type=MapLayerType.ZONE,
        )
        zones = mm.place_voronoi_zones(vcfg)

        gcfg = PlaceGroupsConfig(
            object_type=UnitInfo.MILITIA,
            map_layer_type=MapLayerType.UNIT,
            point_collection=mm.point_manager.get_point_collection("all"),
            groups=min(200, n * n // 50),
            group_size=5,
            player_id=PlayerId.ONE,
            margin=0,
            clumping=0,
        )
        mm.place_groups(gcfg)

    benchmark(run)
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Vectorised Voronoi produces different zone assignments (different L1 tie-breaking) | Medium | Medium | Compare zone coverage statistics, not exact assignments; update snapshot tests accordingly |
| `lru_cache` on `ObjectInfo` with mutable `aoe2_object` args breaks | Low | High | `MapObject` is `@dataclass(frozen=True)` and `PlayerId` is an Enum — both hashable; safe |
| NumPy Perlin differs from pure-Python by floating-point rounding | Low | Low | Use `PerlinNoiseConfig(seed=0)` in determinism tests; allow ±1e-9 tolerance |
| Bounding-box caching in `PointCollection` goes stale on boundary removal | Medium | Medium | Add a `_dirty_bounds` flag; rebuild lazily on next access |
| `pytest-benchmark` not installed — CI blocks | High | Low | Add to `[tool.poetry.dev-dependencies]`; keep benchmarks in a separate `performance/` directory so standard test runs skip them |

---

## Open Questions

- [ ] Should the performance test suite be gated in CI (fail on regression > 10%) or advisory only?
- [ ] Is there an acceptable tolerance for zone-assignment differences after Voronoi vectorisation (e.g. existing snapshot images will change)?
- [ ] Do any callers depend on the *specific* tie-breaking behaviour of the current `generate_voronoi_l1`?
- [ ] Is the `MapLayer` NumPy refactor (Finding 7) within scope for the next milestone?

---

## Implementation Log

> Append entries here when this plan is acted upon. Do not edit prior entries.

<!-- Example entry:
### [YYYY-MM-DD HH:MM UTC] — [Agent or Human ID]
**Status Change:** PLANNED → IN PROGRESS  
**What was done:** ...  
**Commits:** `abc1234` — "perf(voronoi): vectorise l1 voronoi with cKDTree"  
**Notes:** ...  
-->
