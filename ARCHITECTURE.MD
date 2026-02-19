# aoe2mapgenerator Architecture

## Execute Summary

`aoe2mapgenerator` is a map-construction library centered on `MapManager`, which owns a `Map` (five layers) and delegates generation work to placers, wall generators, templates, and serialization/export components.  
The runtime path is: initialize map -> mutate layers through typed operations -> optionally visualize -> serialize/write scenario file.

The architecture is designed so algorithmic building blocks (placers/templates) can evolve independently while maintaining a stable top-level orchestration contract.

## Core Architecture

```text
MapManager
  -> Map (size + 5 MapLayer objects)
  -> Placers (group, wall, gate, base, path)
  -> PointManager / PointSelector
  -> VoronoiGenerator
  -> TemplateManager
  -> Scenario writer (.aoe2scenario)
```

## Domain Model

## `Map`

`src/aoe2mapgenerator/map/map.py`

- Top-level container for all map state.
- Holds five layers:
  - `UNIT`
  - `ZONE`
  - `TERRAIN`
  - `DECOR`
  - `ELEVATION`
- Supports multiple serialization forms (`model_dump` / legacy serialize-deserialize paths).

## `MapLayer`

`src/aoe2mapgenerator/map/maplayer.py`

Each layer maintains dual representations:
- 2D array for coordinate lookup
- dictionary/set structure for object-based lookups

This dual structure supports both positional and semantic operations efficiently.

## `MapObject`

`src/aoe2mapgenerator/map/map_object.py`

Typed tile payload containing object type and player ownership.

## Orchestration: `MapManager`

`src/aoe2mapgenerator/map/map_manager.py`

Primary facade used by callers.

Responsibilities:
- initialize map and collaborators
- expose fluent map-mutating operations
- rewire collaborators when loading a serialized map (`load_map`)
- persist results via `Scenario`

Important invariant:
- after deserializing map state, call `load_map(map_obj)` instead of setting `map` directly so all internal helpers point to the loaded state.

## Mutation Components

## Placers (`units/placers/`)

- `PlacerBase`: low-level placement primitives
- `GroupPlacer`: clustered object placement
- `WallPlacer`: borders and walls
- `GatePlacer`: gate insertion
- `PathPlacer`: path generation
- `placer_configs.py`: typed configs for deterministic call signatures

## Wall Generators (`units/wallgenerators/`)

- `voronoi.py`: Voronoi cell generation and region partitioning

## Point Management

`units/placers/point_management/`

- point collection, filtering, and selection utilities used by placers/templates

## Templates

`src/aoe2mapgenerator/templates/`

- higher-level reusable generation recipes
- managed through `TemplateManager` and template registration helpers
- examples include fort and decor-style templates

## Export and Serialization

## Scenario Export

`src/aoe2mapgenerator/scenario/scenario.py`

- converts map-layer state into AoE2 scenario parser operations
- writes `.aoe2scenario` files
- handles map size updates and unique filename generation

## Serialization

`src/aoe2mapgenerator/serializer/`

- supports object and map serialization/deserialization workflows
- used both for persistence and API transport integrations

## Data Flow

## Generate + Mutate + Save

1. Create `MapManager(map_size, output_dir=...)`.
2. Apply operations (`place_groups`, `place_borders`, templates, Voronoi, etc.).
3. Read current state via `get_map()`.
4. Save with `write_map_and_save(file_name)`.

## API Round-Trip (GeneralWebsite Integration)

1. Backend receives serialized map payload.
2. Converts payload to `Map` object.
3. Creates `MapManager(map_size, output_dir=...)`.
4. Calls `load_map(map_obj)`.
5. Dispatches requested operation.
6. Re-serializes result and returns to frontend.

## Testing Architecture

Primary tests are in `src/aoe2mapgenerator/unit_tests/`:
- map behavior
- border placement
- group placement
- Voronoi behavior
- serialization

Some tests can optionally produce visualization output through flags in `conftest.py`.

## Extension Points

## Add a New Map Operation

1. Implement operation in an existing/new placer.
2. Add a typed config dataclass in `placer_configs.py` if needed.
3. Expose method in `MapManager`.
4. Add tests under `unit_tests/`.

## Add a New Template

1. Implement a template class in `templates/`.
2. Register template type.
3. Wire through `TemplateManager`.
4. Add coverage for expected placement behavior.

## Add External API Access (via GeneralWebsite)

1. Add/adjust function registration in `GeneralWebsite/backend/aoe2_generator/services/function_registry.py`.
2. Ensure arguments map cleanly to `MapManager` methods/configs.
3. Update OpenAPI schema and regenerate frontend client types.

## Known Coupling

- Strong coupling to `AoE2ScenarioParser` dataset enums and file format.
- Cross-repo coupling with `GeneralWebsite` serialization and function dispatch contract.
- Path-dependent scenario output behavior can vary by environment; validate paths when changing constants.
