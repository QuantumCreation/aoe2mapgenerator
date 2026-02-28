# Contributing to aoe2mapgenerator

Thanks for contributing. This guide covers setup, validation, coding conventions, and step-by-step recipes for the two most common extension tasks: **adding a template** and **adding a trigger method**.

---

## Repository Purpose

`aoe2mapgenerator` is a Python library for procedurally generating Age of Empires II scenario maps and exporting `.aoe2scenario` files.

Key package root: `src/aoe2mapgenerator/`.

---

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) (recommended)
- `AoE2ScenarioParser` (installed automatically via `poetry install`)

---

## Local Setup

### Poetry (recommended)

```bash
cd /home/joey/Documents/Projects/aoe2mapgenerator
poetry install
```

### pip editable install

```bash
cd /home/joey/Documents/Projects/aoe2mapgenerator
pip install -e .
```

---

## Running Validation

### Unit tests

```bash
./run_tests.sh
# or
poetry run pytest src/aoe2mapgenerator/unit_tests -q
```

### Type checking

```bash
./run_mypy.sh
# or
poetry run mypy src
```

### Targeted tests

```bash
poetry run pytest src/aoe2mapgenerator/unit_tests/map_test.py -q
poetry run pytest src/aoe2mapgenerator/unit_tests/map_test.py::test_create_map_10 -q
```

---

## Project Areas

| Directory | Purpose |
|---|---|
| `map/` | Core map container, layer management, `MapManager` façade |
| `templates/` | Template definitions registered via `@register_template` |
| `units/placers/` | Placement algorithms and typed config objects |
| `units/wallgenerators/` | Voronoi and wall generation logic |
| `triggers/` | `TriggerManager` and `city_life` trigger helpers |
| `scenario/` | `Scenario` writer and `ScenarioConfig` / `PlayerConfig` |
| `terrain/` | Perlin-noise terrain generator |
| `serializer/` | `SerializedMap` JSON round-trip |
| `unit_tests/` | pytest regression and behavior coverage |

---

## Coding Expectations

- Keep `MapManager` as the primary orchestration surface. All public generation actions should be reachable (directly or indirectly) through it.
- Prefer **typed config dataclasses** (e.g. `PlaceGroupsConfig`) over long positional argument lists.
- All public APIs **must have type hints** (PEP 484/585). Avoid `Any` unless unavoidable and documented.
- Preserve map-layer consistency when introducing new mutating behavior.
- Keep serialization and map-mutation concerns separate.

---

## How to Add a Template

Templates are self-contained generation recipes registered with a `TemplateType` enum value via the `@register_template` decorator.

### 1.  Add an enum value

Edit `src/aoe2mapgenerator/common/enums/enum.py` and add your entry to `TemplateType`:

```python
class TemplateType(str, Enum):
    ...
    MY_TEMPLATE = "MY_TEMPLATE"   # ← new
```

### 2.  Implement the template function

Create or add to an existing file under `src/aoe2mapgenerator/templates/`. Convention:

- Group thematically similar templates in one file (e.g. `nature_templates.py`, `military_templates.py`).
- Use `@register_template(TemplateType.MY_TEMPLATE)` on a function that accepts `(map_manager: IMapManager, ...)`.

```python
# src/aoe2mapgenerator/templates/my_templates.py
from aoe2mapgenerator.templates.template_manager import register_template
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.common.enums.enum import TemplateType, MapLayerType
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId

@register_template(TemplateType.MY_TEMPLATE)
def my_template(map_manager: IMapManager, point: tuple[int, int], size: int) -> None:
    """Short description of what this template places."""
    x, y = point
    map_manager.place_groups(
        MapLayerType.UNIT,
        object_type=UnitInfo.MILITIA,
        point=(x, y),
        size=size,
    )
```

### 3.  Register the import in `map_manager.py`

Open `src/aoe2mapgenerator/map/map_manager.py` and add a side-effect import so the decorator fires at startup:

```python
# --- Template side-effect imports (keep sorted) ---
import aoe2mapgenerator.templates.my_templates  # noqa: F401
```

### 4.  Add a convenience shortcut method (optional but recommended)

Append a thin wrapper to `MapManager` at the bottom of `map_manager.py`:

```python
def create_my_template(self, point: tuple[int, int], size: int = 10) -> "MapManager":
    """Convenience wrapper — apply MY_TEMPLATE at *point* with *size*."""
    return self.apply_template(TemplateType.MY_TEMPLATE, point=point, size=size)
```

### 5.  Write a test

Add a test in `src/aoe2mapgenerator/unit_tests/template_test.py`:

```python
def test_my_template_creates_objects(map_manager_fixture: MapManager) -> None:
    map_manager_fixture.create_my_template(point=(30, 30), size=10)
    # assert some tile was set
    tile = map_manager_fixture.map.get_tile(MapLayerType.UNIT, 30, 30)
    assert tile is not None
```

---

## How to Add a TriggerManager Method

All trigger helpers live in `src/aoe2mapgenerator/triggers/triggers.py` as methods of `TriggerManager`.

### 1.  Look up the AoE2ScenarioParser API

The two key modules to check:

```python
from AoE2ScenarioParser.scenarios.scenario_store.trigger_manager import NewEffectSupport
from AoE2ScenarioParser.datasets.trigger_lists import EffectId
```

- `NewEffectSupport` exposes helper methods like `new_effect.change_diplomacy(...)` or `new_effect.modify_resource(...)`.
- `EffectId` enumerates all available effect IDs.

### 2.  Add the method to `TriggerManager`

```python
def my_trigger(
    self,
    player_id: int,
    my_param: int,
    trigger_name: str = "my_trigger",
) -> None:
    """Brief doc: what this trigger does at run-time."""
    trigger = self.trigger_manager.add_trigger(trigger_name)
    effect = trigger.new_effect.my_effect_name(
        source_player=player_id,
        # ... effect-specific kwargs
    )
    _ = effect  # suppress unused-variable warnings if needed
```

### 3.  Write a test

Add a test in `src/aoe2mapgenerator/unit_tests/triggers_test.py` (or create one following the existing pattern):

```python
def test_my_trigger_creates_trigger(map_manager_fixture: MapManager) -> None:
    map_manager_fixture.triggers.my_trigger(player_id=1, my_param=500)
    triggers = map_manager_fixture.triggers.trigger_manager.triggers
    assert any(t.name == "my_trigger" for t in triggers)
```

---

## Test Expectations

- Add or update tests for all behaviour changes.
- Keep new tests **deterministic**: pass a `seed` to `MapManager` and use fixed coordinates.
- Visual / regression output changes must be documented in the PR.
- The `@_requires_aoe2` skip marker is used for tests that need the full AoE2 installation — add it only when unavoidable.

---

## Pull Request Checklist

1. Implement the change with focused scope (one concern per PR).
2. Add / update tests in `src/aoe2mapgenerator/unit_tests/`.
3. Run `./run_tests.sh` and `./run_mypy.sh`; paste summary output.
4. Update `README.md`, `API_REFERENCE.md`, or architecture docs if public behaviour changed.
5. PR description must include:
   - **What** changed
   - **Why**
   - Commands run and their results

---

## Integration Note (GeneralWebsite)

`GeneralWebsite/backend` consumes this library through a local path dependency:

```toml
# GeneralWebsite/backend/pyproject.toml
aoe2mapgenerator = { path = "../../aoe2mapgenerator", develop = true }
```

If you change serialization contracts or `MapManager` behaviour, also update:
- `GeneralWebsite/backend/aoe2_generator/services/save_service.py`
- `GeneralWebsite/backend/aoe2_generator/schemas.py`
- `GeneralWebsite/backend/aoe2_generator/openapi/components.yaml`
- Re-run `npm run generate:api` in `GeneralWebsite/frontend/` to regenerate TypeScript types.
