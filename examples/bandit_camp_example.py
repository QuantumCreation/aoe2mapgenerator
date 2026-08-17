"""
bandit_camp_example.py
======================
Demonstrates the BANDIT_CAMP and BERRY_BUSH content-toolkit templates: a
hostile camp (dirt patch, bonfire, tent ring, bandits) set in a lightly
foraged grassland.

Run:
    poetry run python examples/bandit_camp_example.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, cx: int, cy: int, half: int):
    """Add a square PointCollection centred on (cx, cy) with the given half-size."""
    mg.point_manager.add_point_collection(name)
    pc = mg.point_manager.get_point_collection(name)
    size = mg.map.size
    pc.add_points([
        (x, y)
        for x in range(max(0, cx - half), min(size, cx + half))
        for y in range(max(0, cy - half), min(size, cy + half))
    ])
    return pc


def main() -> None:
    size = 120
    mg = MapManager(size, output_dir=OUTPUT_DIR, seed=11)

    # Base grassland (GRASS_OTHER avoids the id-0 empty-sentinel collision).
    all_pts = make_region(mg, "all", size // 2, size // 2, size // 2)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_pts,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_OTHER,
        groups_density=1.0,
        group_size=1,
    ))

    # A bandit camp in the centre of the map.
    camp_pts = make_region(mg, "camp", 60, 60, 20)
    mg.create_bandit_camp(
        point_collection=camp_pts,
        center_point=(60, 60),
        size=14,
        tents=6,
        bandits=8,
    )

    # Scatter berry bushes across the surrounding grassland.
    mg.create_berry_bush(point_collection=all_pts, density=0.02)

    mg.write_map_and_save("bandit_camp_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/bandit_camp_example.aoe2scenario")


if __name__ == "__main__":
    main()
