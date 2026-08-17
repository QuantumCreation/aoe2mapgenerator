"""
snowy_mountains_example.py
==========================
Demonstrates the SNOWY_MOUNTAIN_RANGE and FAUNA_SCATTER content-toolkit
templates: an elongated snow-mountain ridgeline with a wildlife population
scattered across the surrounding tundra.

Run:
    poetry run python examples/snowy_mountains_example.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, x0: int, y0: int, x1: int, y1: int):
    """Add a rectangular PointCollection over [x0, x1) x [y0, y1)."""
    mg.point_manager.add_point_collection(name)
    pc = mg.point_manager.get_point_collection(name)
    size = mg.map.size
    pc.add_points([
        (x, y)
        for x in range(max(0, x0), min(size, x1))
        for y in range(max(0, y0), min(size, y1))
    ])
    return pc


def main() -> None:
    size = 120
    mg = MapManager(size, output_dir=OUTPUT_DIR, seed=23)

    # Base grassland (GRASS_OTHER avoids the id-0 empty-sentinel collision).
    all_pts = make_region(mg, "all", 0, 0, size, size)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_pts,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_OTHER,
        groups_density=1.0,
        group_size=1,
    ))

    # An elongated snow-mountain ridgeline running east-west.
    ridge_pts = make_region(mg, "ridge", 10, 35, 110, 85)
    mg.create_snowy_mountain_range(point_collection=ridge_pts, max_elevation=6)

    # A wildlife population scattered across the whole map.
    mg.create_fauna_scatter(point_collection=all_pts, herd_count=8, predator_count=4)

    mg.write_map_and_save("snowy_mountains_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/snowy_mountains_example.aoe2scenario")


if __name__ == "__main__":
    main()
