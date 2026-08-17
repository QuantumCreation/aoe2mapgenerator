"""
lush_forest_example.py
======================
Demonstrates the LUSH_FOREST content-toolkit template: a dense mixed forest
with clearings, berry bushes, and a little fauna, set on a grass base.

Run:
    poetry run python examples/lush_forest_example.py
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
    mg = MapManager(size, output_dir=OUTPUT_DIR, seed=37)

    # Base grassland (GRASS_OTHER avoids the id-0 empty-sentinel collision).
    all_pts = make_region(mg, "all", size // 2, size // 2, size // 2)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_pts,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_OTHER,
        groups_density=1.0,
        group_size=1,
    ))

    # A dense mixed forest covering the whole map, with a few clearings.
    mg.create_lush_forest(point_collection=all_pts, tree_density=0.15, clearings=4)

    mg.write_map_and_save("lush_forest_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/lush_forest_example.aoe2scenario")


if __name__ == "__main__":
    main()
