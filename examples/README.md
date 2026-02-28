# aoe2mapgenerator — Examples

Each script demonstrates a different capability of the library. All write their
output to `/tmp/`. Adjust `OUTPUT_DIR` at the top of each file to point at
your AoE2 DE scenario folder if you want to load the maps directly in-game.

## Running an example

```bash
# From the repository root
poetry run python examples/basic_map.py
```

## Scripts

| Script | What it demonstrates |
|---|---|
| [basic_map.py](basic_map.py) | Minimal end-to-end: terrain fill + unit placement |
| [terrain_example.py](terrain_example.py) | Perlin-noise terrain with multiple terrain bands |
| [city_example.py](city_example.py) | CITY template with surrounding oak forests |
| [nature_example.py](nature_example.py) | Oak and pine forest biomes scattered across the map |
| [mine_mountain_example.py](mine_mountain_example.py) | MINE + MOUNTAIN templates + player forts |
| [castle_road_example.py](castle_road_example.py) | CASTLE + ROAD + WALLS templates — two opposing castles |
| [scenario_config_example.py](scenario_config_example.py) | `ScenarioConfig` / `PlayerConfig` — civilizations, ages, diplomacy |

## Notes

- Scripts that call `mg.write_map_and_save()` or `mg.configure_scenario()` require a valid
  AoE2 DE installation with a base scenario file at the path configured in
  `aoe2mapgenerator/common/constants/constants.py`.
- All scripts accept a `seed` argument on `MapManager` for deterministic output.
- `PointCollection` objects are the primary way to specify tile regions; use the
  `make_region` helper pattern shown in each script.
