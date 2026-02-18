# aoe2mapgenerator — Architecture

## Overview

`aoe2mapgenerator` is a Python library for procedurally generating Age of Empires 2
scenario maps.  The high-level flow is:

```
MapManager
  ├─ Map  (Pydantic model — owns all layer state)
  │    └─ MapLayer × 5  (UNIT | ZONE | TERRAIN | DECOR | ELEVATION)
  │         └─ MapObject  (obj_type + player_id per tile)
  ├─ Placers  (GroupPlacer, WallPlacer, GatePlacer, PlacerBase)
  ├─ VoronoiGenerator  (Voronoi-cell zone assignment)
  ├─ PointManager / PointSelector  (spatial point queries)
  ├─ TemplateManager  (registered high-level templates)
  └─ Scenario  (AoE2ScenarioParser wrapper → writes .aoe2scenario files)
```

---

## Module Responsibilities

### `map/`

| File | Purpose |
|---|---|
| `map.py` | Top-level `Map` Pydantic model. Holds five `MapLayer` instances. Owns `model_dump()` / `model_validate()` and legacy `serialize()` / `deserialize()`. |
| `maplayer.py` | Single `MapLayer`: a 2-D `array` + inverse `dictionary` of `MapObject → set[Point]`. All mutations go through `set_point()`. |
| `map_object.py` | Immutable value object: `(obj_type, player_id)` pair placed on a tile. |
| `map_manager.py` | **Main entry point.** Façade over all sub-systems; provides the fluent API used by callers. |
| `imap_manager.py` | `Protocol` defining the stable public contract for `MapManager`. Templates and services should type-hint against `IMapManager`. |

### `units/placers/`

| File | Purpose |
|---|---|
| `placer_base.py` | Low-level tile placement: `place_object`, `check_placement`, margin enforcement. |
| `group_placer.py` | Places groups of objects with configurable density, clumping, and size. |
| `wall_placer.py` | Adds walls / borders along the perimeter of a region. |
| `gate_placer.py` | Inserts gate objects at wall openings. |
| `placer_configs.py` | Dataclass configs for every placer method — keeps call-sites clean. |
| `point_management/` | `PointCollection` (ordered point set) + `PointManager` + `PointSelector`. |

### `units/wallgenerators/`

| File | Purpose |
|---|---|
| `voronoi.py` | Assigns map tiles to Voronoi cells; used to create distinct zone regions. |

### `templates/`

High-level, reusable map recipes built on top of `MapManager`.

| File | Purpose |
|---|---|
| `templates_manager.py` | Registry + dispatcher for named templates. |
| `template_decorator.py` | `@register_template` decorator + `get_template_manager()` factory. |
| `template_types.py` | `TemplateType` enum (e.g. `FORT`, `OAK_FOREST`). |
| `decor.py` | `OakForestTemplate` and other decoration templates. |
| `fort.py` | `FortTemplate` — walls + gates around a square region. |

### `scenario/`

Thin wrapper around `AoE2ScenarioParser` that converts the internal `Map` model into
a writable `.aoe2scenario` file.

### `serializer/`

`Serializable` base class + helpers for converting `MapLayerType`, `PlayerId`, and
other enum values to/from their string representations used in JSON.

### `common/`

| Path | Purpose |
|---|---|
| `enums/enum.py` | Project-wide enums: `MapLayerType`, `GateType`, `GateObject`, `CheckPlacementReturnTypes`, object catalogues (`DecorObjectsOverlap`, etc.). |
| `constants/constants.py` | File-system paths, default values, displacement constants. |
| `constants/default_objects.py` | Default `MapObject` sentinels (empty tile, ghost displacement). |
| `types.py` | Type aliases: `AOE2ObjectType`, `Point`. |

### `visualizer/`

Matplotlib-based map renderer used during development / debugging.

---

## Data Flow

1. **Create a `MapManager`** with a map size.  This creates an empty `Map` (all tiles
   are `DEFAULT_EMPTY_OBJECT`).

2. **Populate zones** (optional) — call `place_voronoi_zones()` to assign tiles to
   named Voronoi-cell regions held in the ZONE layer.

3. **Place objects** — call `place_groups()`, `place_borders()`, or a template like
   `create_oak_forest()` / `create_fort()`.  Each operation reads/writes `Map` via
   `MapLayer.set_point()`.

4. **Save** — call `write_map_and_save(filename)`.  `Scenario` reads the `Map`,
   creates `AoE2ScenarioParser` objects for every non-empty tile, and writes the
   `.aoe2scenario` binary.

---

## How to Add a New Placer

1. Create `units/placers/my_placer.py` subclassing `PlacerBase`.
2. Add a config dataclass to `placer_configs.py`.
3. Register the placer as an attribute in `MapManager.__init__`.
4. Add a delegating method on `MapManager` (returns `self` for chaining).
5. Add the method stub to `IMapManager`.

## How to Add a New Template

1. Create `templates/my_template.py` with a class exposing a static `generate()`
   method accepting `(map_manager: IMapManager, point_collection, **kwargs)`.
2. Add a member to `TemplateType` enum in `template_types.py`.
3. Decorate the class (or register manually) via `template_decorator.py`.
4. Optionally add a convenience method on `MapManager` (e.g. `create_my_template()`).
