# Interesting Shape Generation — Algorithms & Iteration Loop

Date: 2026-08-16
Status: DRAFT
Companion to: `2026-08-16_map-content-toolkit-plan.md`

Two parts:
1. **Algorithms & patterns** for generating interesting shapes (cities, walls,
   settlements, terrain features).
2. **A concrete iteration loop** for running small generations, checking
   whether the output looks good, and improving — with both automated metrics
   and human-in-the-loop review.

---

## Part 1 — Algorithms & Patterns for Interesting Shapes

### 1.1 The core problem

"Interesting" in a map shape means roughly:
- **Even coverage** — no clumps and no gaps (perceived fairness/quality)
- **Organic irregularity** — not a perfect grid, but not pure noise either
- **Coherent structure** — local rules that produce global meaning (streets,
  districts, ridgelines)
- **Variety under constraint** — same genre, different result per seed

Almost every good procedural shape system is a combination of:
**sampling** (where do things go?) + **structure** (how are they connected?)
+ **dressing** (what fills the space?).

### 1.2 Sampling — where do things go?

| Algorithm | What it gives you | Use in AoE2 maps |
|---|---|---|
| **Jittered grid** (grid + random offset per cell) | Even coverage, cheap, deterministic | Default for tree clusters, berry bushes, farm placement. Already close to what `GroupPlacer` does with `groups_density`/`clumping` |
| **Poisson disk sampling** (Bridson's algorithm) | Guaranteed minimum distance, organic evenness | Building placement inside cities/villages — prevents overlap while looking natural. Best upgrade for settlement interiors |
| **Voronoi / Delaunay** | Natural partitioning, irregular polygons | Already used (`wallgenerators/voronoi.py`, `place_voronoi_zones`). Use for: district boundaries, fort wall shapes, mine/mountain cluster shapes |
| **Space colonization** (SCA) | Trees/roads that grow toward evenly spaced targets | Road networks: seed target points (buildings, map edges), grow a tree that branches toward the nearest unconnected target. Produces the "organic medieval road" look |
| **Random walk / drunkard's walk** | Meandering paths, rivers | River segments, dirt paths between buildings (we have `PathPlacer`; a walk-based variant gives more natural meander) |
| **Fibonacci sphere / lattice** | Perfectly even angular distribution | Gate placement around circular forts, tower spacing on round walls |

**Recommendation:** add a small `sampling.py` utility module with
`jittered_grid()`, `poisson_disk()`, and `space_colonization()` as pure
functions `(region, n, min_dist, rng) -> list[Point]`. Pure functions =
trivially unit-testable and reusable by every template.

### 1.3 Structure — how are things connected?

#### Cities & settlements

1. **Road-first generation** (the classic, used by most city generators):
   1. Pick a center (or 2–3 centers for larger cities).
   2. Generate a road skeleton: 3–6 primary roads radiating from center at
      jittered angles (not exactly 90° — jitter ±20° for organic feel),
      optionally with a ring road connecting them.
   3. Subdivide the regions between roads into **blocks** (Voronoi cells
      clipped to the region, or simple rectangular subdivision with jittered
      boundaries).
   4. Assign each block a **district type** (residential, market, military,
      religious, elite) using a weighted random walk so similar districts
      cluster (Markov-chain district assignment).
   5. Place buildings inside blocks with Poisson disk sampling, oriented to
      the nearest road.
   6. Walls/gates go on the outer boundary; gates align to primary roads.

   This is exactly the right shape for our existing `CityTemplate` district
   system — the current prefab stamper can become the "dressing" step on top
   of a generated road/block skeleton.

2. **Concentric rings** (medieval feel): center = palace/TC, ring 1 = elite
   homes, ring 2 = market, ring 3 = residential, ring 4 = walls + towers.
   Jitter ring radii and building angles. Cheap, looks good, easy to
   parameterize. Good default for `compact` preset.

3. **L-systems** (grammar-based growth): define rules like
   `F -> F[+F]F[-F]F` and walk the map executing forward/turn commands.
   Great for **roads, rivers, and tree lines** — produces branching,
   self-similar structure. Overkill for buildings; perfect for the
   "castle road" and river templates.

#### Walls & fortifications

1. **Polygon offsetting**: take an inner polygon (keep), offset outward by a
   wall thickness, place towers at vertices. We have this in
   `wallgenerators/polygon.py` — the upgrade is **vertex jitter + corner
   variation** (some corners get towers, some get angled walls, some get
   gate notches).
2. **Voronoi cell walls**: pick N seed points on a circle (jittered radius),
   take the Voronoi cell containing the center, use its boundary as the wall
   line. Already exists (`voronoi.py`) — add gate insertion at the cell edge
   closest to a road.
3. **Perlin-perturbed circles**: radius(θ) = R + A·noise(θ). Smooth organic
   walls. We have `wallgenerators/perlin.py` — tune amplitude so walls read
   as "hand-built" not "blob".
4. **Moats & baileys** (for the fortress tier): generate outer wall, carve a
   water ring (moat) at fixed offset, inner keep polygon inside. Bridges at
   gates. Pure geometry — no new machinery.

#### Terrain features

1. **Ridgeline noise** for mountains: `1 - |perlin(x, y)|` (abs creates
   ridges). Combine with a directional mask for a *range* (elongated
   ridgeline) instead of scattered bumps. This is the key upgrade for
   `SnowyMountainRangeTemplate`.
2. **Domain warping**: `perlin(x + warp·perlin(x), y + warp·perlin(y))` —
   makes coastlines, forest edges, and river banks look natural instead of
   blobby. Cheap, huge visual win.
3. **Cellular automata** (grow/shrink): seed a blob, iterate
   "cell survives if ≥ N neighbors survive". Produces natural-looking
   coastlines, lake shapes, forest patches. 4–6 iterations is usually enough.
   Great for ponds/lakes that look hand-drawn.
4. **Erosion (hydraulic, simplified)**: drop random water drops that carve
   downward along gradients. Even a toy version (100 drops, steepest-descent
   step) makes flat Perlin terrain look like real eroded land with valleys.
   Optional — expensive, but a "cheap erosion" pass is a known good trick.

### 1.4 Dressing — filling the space

- **Weighted scatter with clumping**: pick cluster centers (Poisson disk),
  then scatter objects around each center with a Gaussian falloff. This is
  the "trees look like a forest, not confetti" trick. Our `GroupPlacer`
  `clumping` parameter is a crude version; a proper two-stage
  (centers → gaussian scatter) is the upgrade.
- **Edge-aware placement**: trees/bushes avoid water and roads (check
  neighbor tiles), berries prefer forest edges (distance-to-boundary band),
  animals prefer open clearings near forest. Implement as per-object-type
  **placement predicates** over the terrain layer.
- **Palette + noise**: pick 3–4 terrain variants per biome and blend them
  with low-frequency noise instead of one flat terrain id — instantly less
  "generated-looking".

### 1.5 Variety & determinism

- **One seed, everything derived**: a single `np.random.Generator` (or
  `random.Random(seed)`) passed through every stage. Same seed → same map.
  Different seed → different but same-genre map. (We already have `seed` on
  `MapManager` — make sure templates draw from it, not from global `random`.)
- **Parameter ranges, not fixed values**: every "magic number" (road count,
  ring radii, jitter amplitude) becomes a parameter with a sensible default
  and a range. The recipe layer (toolkit plan, phase 5) samples from ranges.
- **Style presets = parameter bundles**: "trading city" isn't new code, it's
  `{district_weights: {...}, road_count: 5, ring_road: true, ...}`.

### 1.6 Suggested algorithm assignments (concrete)

| Feature | Primary algorithm | Secondary |
|---|---|---|
| City layout | Road skeleton + Voronoi blocks + Markov districts | Concentric rings for compact preset |
| Village | Concentric rings (2 rings) + jitter | — |
| Fort/fortress walls | Jittered polygon + vertex towers | Voronoi cell, perlin circle |
| Bandit camp | Small concentric layout (campfire center, tents ring) | — |
| Roads/paths | Space colonization toward targets | L-system for decorative branches |
| Rivers | Random walk with momentum + domain-warped banks | L-system |
| Mountains | Ridgeline noise + directional mask | Erosion pass (optional) |
| Forests/berries | Poisson cluster centers + Gaussian scatter | Edge-aware predicates |
| Ponds/lakes | Cellular automata blob smoothing | — |
| Terrain blending | Low-frequency noise palette blend | — |

---

## Part 2 — The Iteration Loop

Goal: change generation logic → see the result in **under a minute** → judge
quality (automated + human) → repeat.

### 2.1 What we already have (ground truth)

- `MapManager.visualize_map(VisualizeMapConfig)` → matplotlib render of any
  layer (terrain, objects, zones) with legend. Saves/shows a figure.
- `MapManager.get_array(MapLayerType)` → raw 2D numpy-able matrix of
  `MapObject`s. **This is the key hook**: everything below works on this
  matrix without needing matplotlib or a game.
- `./run_tests.sh` → poetry install + pytest.
- `examples/*.py` pattern → one script per feature, writes to `/tmp/`.
- `MapManager(seed=...)` → deterministic output.

### 2.2 The loop, in four tiers

#### Tier 0 — Headless metrics (seconds, no display, CI-able)

A script `tools/evaluate_map.py` that builds a map and prints a **quality
report** computed from `get_array()` matrices. Metrics:

| Metric | What it catches | How |
|---|---|---|
| **Coverage** | Empty patches / wasted space | % of tiles non-empty per layer; min tile count per expected object type |
| **Overlap / collision** | Buildings on water, trees inside walls | Cross-layer predicate checks (e.g. building tile must be land; wall tile must not contain a tree) |
| **Connectivity** | Disconnected roads, unreachable gates | BFS over road tiles from each gate; all must reach the settlement center |
| **Evenness (Gini / nearest-neighbor)** | Clumpy or gappy scatter | For scattered objects (trees, berries): compute nearest-neighbor distance distribution; report mean ± std. Healthy scatter ≈ tight distribution; clumps ≈ wide |
| **Symmetry / regularity** | Too-perfect or too-chaotic | Variance of wall segment lengths; angle histogram of roads (all 90° = boring, all random = chaotic) |
| **Bounds** | Objects off-map or on border | Min/max coords per layer |
| **Determinism** | Seed broken | Build twice with same seed → matrices identical |

Output: a one-screen text report with PASS/WARN/FAIL per metric. This runs in
CI and locally in < 5 s. **This is the gate: a change doesn't get reviewed
visually until metrics pass.**

#### Tier 1 — Fast visual (seconds, local)

`tools/render_map.py`:
1. Build the map (same recipe call as Tier 0).
2. Render **one composite PNG** per map: terrain layer as base color,
   objects as colored dots/shapes per category (buildings, walls, trees,
   water, units), gates highlighted. Use matplotlib `imshow` on the
   `get_array()` matrix — no per-tile `hlines` (the current
   `visualize_mat` is slow for large maps; `imshow` is ~100× faster).
3. Write to `tools/out/<name>_<seed>.png`.

A **contact sheet** mode: `tools/render_map.py --seeds 1..8` renders 8 seeds
of the same recipe into one 4×4 grid PNG. This is the single most useful
artifact for judging "does this algorithm produce *variety* as well as
quality" — you see 8 outcomes at a glance.

#### Tier 2 — Human review (minutes)

- Open the contact sheet, eyeball it. Verdict per seed: keep / tweak / kill.
- For anything promising: `write_map_and_save()` → load in AoE2 DE (the real
  test — tile art, scale, and gameplay feel can't be faked by matplotlib).
- Keep a `tools/out/review.md` scratch log: date, recipe, seed, verdict,
  one-line note. This becomes the design history.

#### Tier 3 — Regression (per commit)

- **Golden seeds**: pick 3–5 seeds that produce known-good maps for each
  template. Commit their metric reports (and optionally the PNGs, or their
  hashes) as fixtures.
- A pytest that rebuilds each golden seed and asserts: metrics still pass +
  object counts within tolerance. Catches "my wall change quietly broke
  village gates" regressions.
- Full suite: `./run_tests.sh`.

### 2.3 The concrete workflow (what I will do per change)

```
1. Edit template/algorithm code
2. poetry run python tools/evaluate_map.py --recipe <name> --seed 42
      → metrics report (must be all PASS)
3. poetry run python tools/render_map.py --recipe <name> --seeds 1..8
      → contact sheet PNG
4. View PNG (view_image) → self-check: clumps? overlaps? dead zones?
5. If good: add/extend unit test + golden-seed fixture
6. ./run_tests.sh → full suite green
7. (For big features) write_map_and_save → user loads in AoE2 DE
```

Steps 2–4 are the inner loop (~30 s). Step 7 is the outer loop (you, in-game).

### 2.4 Implementation plan for the tooling

| Item | File | Notes |
|---|---|---|
| Sampling utilities | `src/aoe2mapgenerator/utils/sampling.py` | `jittered_grid`, `poisson_disk`, `space_colonization` — pure functions, unit-tested |
| Metric evaluators | `src/aoe2mapgenerator/evaluation/metrics.py` | Pure functions over `get_array()` matrices; no I/O |
| CLI: evaluate | `tools/evaluate_map.py` | Builds recipe, prints report, exit code = pass/fail |
| CLI: render | `tools/render_map.py` | `imshow`-based fast renderer + `--seeds` contact sheet |
| Golden seed tests | `src/aoe2mapgenerator/unit_tests/golden_seed_test.py` | Parametrized over (template, seed) fixtures |
| Recipe registry | `src/aoe2mapgenerator/recipes.py` | Named recipes (dicts) shared by tools + tests + later frontend |

Order: `sampling.py` → `metrics.py` + `evaluate_map.py` → `render_map.py`
→ golden tests. The tools are useful immediately, before any new template
exists (run them on the existing city/fort/village examples first — that
also establishes baseline metric values).

### 2.5 Definition of "looks good" (acceptance criteria)

A generated feature is "good" when, on the contact sheet:
1. No visible overlaps or objects on wrong terrain (also enforced by Tier 0).
2. Scatter reads as intentional — even density, no clumps > 2× local density.
3. Structure reads at a glance — you can identify "city", "fort", "river"
   without being told.
4. 8 seeds give 8 visibly different layouts (variety check).
5. In-game (Tier 2): scale feels right vs. units, no floating/orphaned
   objects, gates/roads align.

If a metric and the eye disagree, the eye wins — then the metric gets fixed
to match.
