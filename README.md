# aoe2mapgenerator

A Python library for **procedurally generating Age of Empires II Definitive Edition maps** and exporting them as `.aoe2scenario` files.

---

## What it does

- Build layered tile maps (terrain, units, decor, elevation, zones) programmatically.
- Apply reusable **templates** — forests, cities, forts, mines, castles, roads, rivers, and more.
- Generate organic terrain shapes with **Perlin-noise** and **Voronoi** partitioning.
- Fire **triggers** (patrol routes, visibility, resources, win/loss, diplomacy).
- Configure per-player settings (civilization, resources, starting age) via `ScenarioConfig`.
- Write the final map straight to a `.aoe2scenario` file that AoE2 DE can load.

---

## Quick Start

### 1 — Install

```bash
# Clone the repo (if not already present)
git clone https://github.com/your-org/aoe2mapgenerator
cd aoe2mapgenerator

# Install with Poetry (recommended)
poetry install

# — or — editable pip install
pip install -e .
```

### 2 — Generate a map

```python
from aoe2mapgenerator import MapManager, Map, ScenarioConfig, PlayerConfig
from aoe2mapgenerator import PlayerId, Civilization, StartingAge

# Create a 120×120 map
map_obj = Map(120)
mg = MapManager(map_obj, seed=42)

# Apply premade templates
mg.create_oak_forest(point=(20, 20), size=15)
mg.create_city(point=(60, 60), size=40, player_id=PlayerId.ONE)
mg.create_mine(point=(30, 80), size=8)

# Optional: configure scenario metadata
config = ScenarioConfig(
    map_name="My Scenario",
    players=[
        PlayerConfig(player_id=PlayerId.ONE, name="Human", civilization=Civilization.BRITONS),
        PlayerConfig(player_id=PlayerId.TWO, name="AI",    civilization=Civilization.FRANKS),
    ],
    enemy_pairs=[(PlayerId.ONE, PlayerId.TWO)],
)
mg.configure_scenario(config)

# Write to disk
mg.write_map_and_save("/tmp/my_map.aoe2scenario")
```

---

## Features

| Feature | Description |
|---|---|
| **Templates** | Forests, cities, forts, palaces, mines, mountains, castles, roads, rivers, walls |
| **Perlin terrain** | Smooth randomised terrain layers via `PerlinTerrainGenerator` |
| **Voronoi zones** | Divide the map into player/biome zones with `PlaceBorders` |
| **Triggers** | Patrol, visibility, resources, win/loss, diplomacy, unit stance |
| **Scenario config** | Per-player civilization, age, resources, population cap, allied victory |
| **Serialization** | JSON round-trip with `SerializedMap` for saving/restoring map state |
| **Type-safe** | Full PEP 484 type hints; `py.typed` marker included |

---

## API Overview

```
MapManager          — primary orchestration façade
  .create_<name>()  — shortcut template methods (forest, city, port, mine, …)
  .place_groups()   — low-level object placement
  .place_borders()  — Voronoi zone generation
  .configure_scenario(ScenarioConfig) — set player & diplomacy metadata
  .write_map_and_save(path) — write .aoe2scenario

TriggerManager      — attach AoE2 triggers to the scenario
  .add_patrol_path()
  .set_player_wins() / .set_player_loses()
  .set_starting_resources()
  .set_mutual_alliance()
  .reveal_area_to_player()
  … (see triggers.py for the full list)

ScenarioConfig / PlayerConfig
  — dataclasses for per-player settings (civ, age, resources, diplomacy)
```

Full API reference: [`API_REFERENCE.md`](API_REFERENCE.md).

---

## Running Tests

```bash
# All tests (116 passing)
./run_tests.sh

# Or directly with Poetry
poetry run pytest src/aoe2mapgenerator/unit_tests -q

# Single test file
poetry run pytest src/aoe2mapgenerator/unit_tests/map_test.py -q
```

> **Note:** One test (`test_city_life_triggers_created`) is skipped unless a valid AoE2 base scenario file is present at `~/Documents/DE/Games/…`

## Type Checking

```bash
poetry run mypy src
# or
./run_mypy.sh
```

---

## Project Structure

```
src/aoe2mapgenerator/
├── __init__.py          # Public API surface (import from here)
├── map/                 # MapManager, Map, layers
├── templates/           # Template definitions + registry
├── units/               # Object placers and wall generators
├── triggers/            # TriggerManager + city_life
├── scenario/            # Scenario writing + ScenarioConfig
├── terrain/             # Perlin noise generator
├── serializer/          # JSON serialization
├── utils/               # Point collections, helpers
└── unit_tests/          # pytest test suite
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding conventions, testing expectations, and a step-by-step guide for adding new templates and triggers.

5) Advanced / debugging options:

- Run with verbose output: `poetry run pytest -v`
- Use `-k <expr>` to filter tests by keyword (e.g. `-k create_map`).
- Add `--maxfail=1` to stop on first failure.

If you run tests without Poetry you can still use `pytest` directly, but make sure the Python environment contains the project dependencies.
