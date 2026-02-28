"""
scenario_config_example.py
===========================
Demonstrates the full scenario-configuration API:
  - Per-player civilization, starting age, and resource overrides
  - Diplomacy pairs (enemies / allies)
  - TriggerManager: patrol triggers and a victory condition

Run:
    poetry run python examples/scenario_config_example.py

NOTE: Saving the scenario requires a valid AoE2 DE base scenario file at the
path configured in ``aoe2mapgenerator.common.constants.constants``.
Otherwise the write step will raise a FileNotFoundError.
"""

from aoe2mapgenerator import (
    MapManager,
    MapLayerType,
    PlaceGroupsConfig,
    ScenarioConfig,
    PlayerConfig,
    Civilization,
    StartingAge,
)
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def main() -> None:
    SIZE = 100
    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=42)

    # ── Terrain ──────────────────────────────────────────────────────────────
    mg.point_manager.add_point_collection("all")
    all_pts = mg.point_manager.get_point_collection("all")
    all_pts.add_points([(x, y) for x in range(SIZE) for y in range(SIZE)])

    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_pts,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_1,
        groups_density=1.0,
        group_size=1,
    ))

    # ── Scenario metadata + player config ────────────────────────────────────
    config = ScenarioConfig(
        map_name="Kingdoms at War",
        instructions=(
            "Two kingdoms face off. Collect resources and destroy your enemy!"
        ),
        players=[
            PlayerConfig(
                player_id=PlayerId.ONE,
                name="The Britons",
                civilization=Civilization.BRITONS,
                starting_age=StartingAge.CASTLE_AGE,
                starting_food=500,
                starting_wood=500,
                starting_gold=300,
                starting_stone=300,
                population_cap=200,
            ),
            PlayerConfig(
                player_id=PlayerId.TWO,
                name="The Franks",
                civilization=Civilization.FRANKS,
                starting_age=StartingAge.CASTLE_AGE,
                starting_food=500,
                starting_wood=500,
                starting_gold=300,
                starting_stone=300,
                population_cap=200,
            ),
        ],
        enemy_pairs=[(PlayerId.ONE, PlayerId.TWO)],
    )
    mg.configure_scenario(config)

    # ── Write scenario ────────────────────────────────────────────────────────
    mg.write_map_and_save("scenario_config_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/scenario_config_example.aoe2scenario")


if __name__ == "__main__":
    main()
