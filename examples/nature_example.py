"""
nature_example.py
=================
Demonstrates placing multiple nature biomes — oak forests, pine forests —
across a map to produce a diverse landscape.

Run:
    poetry run python examples/nature_example.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, cx: int, cy: int, half: int):
    """Create a square region centred at (cx, cy) with half-width `half`."""
    mg.point_manager.add_point_collection(name)
    pc = mg.point_manager.get_point_collection(name)
    SIZE = mg.map.size
    pc.add_points([
        (x, y)
        for x in range(max(0, cx - half), min(SIZE, cx + half))
        for y in range(max(0, cy - half), min(SIZE, cy + half))
    ])
    return pc


def main() -> None:
    SIZE = 120
    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=99)

    # Base terrain  
    all_points = make_region(mg, "all", SIZE // 2, SIZE // 2, SIZE // 2)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_points,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_1,
        groups_density=1.0,
        group_size=1,
    ))

    # Scatter forest clusters around the edges — alternating oak and pine
    cluster_positions = [
        (15, 15), (15, 60), (15, 105),
        (60, 15), (60, 105),
        (105, 15), (105, 60), (105, 105),
    ]
    for i, (cx, cy) in enumerate(cluster_positions):
        pc = make_region(mg, f"forest_{i}", cx, cy, 12)
        if i % 2 == 0:
            mg.create_oak_forest(point_collection=pc, groups_density=0.07, group_size=8, clumping=3)
        else:
            mg.create_pine_forest(point_collection=pc, groups_density=0.07, group_size=8, clumping=3)

    mg.write_map_and_save("nature_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/nature_example.aoe2scenario")


if __name__ == "__main__":
    main()
