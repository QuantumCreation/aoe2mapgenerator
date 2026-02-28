"""
city_example.py
===============
Places a walled city on a grass map using the built-in CITY template, plus
surrounding oak forest clusters in the corners.

Run:
    poetry run python examples/city_example.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig, GateType
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, x0: int, y0: int, x1: int, y1: int):
    mg.point_manager.add_point_collection(name)
    pc = mg.point_manager.get_point_collection(name)
    SIZE = mg.map.size
    pc.add_points([
        (x, y) for x in range(max(0, x0), min(SIZE, x1))
        for y in range(max(0, y0), min(SIZE, y1))
    ])
    return pc


def main() -> None:
    SIZE = 120
    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=3)

    # Base grass terrain
    all_points = make_region(mg, "all", 0, 0, SIZE, SIZE)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_points,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_1,
        groups_density=1.0,
        group_size=1,
    ))

    # City for player 1 in the centre
    city_points = make_region(mg, "city_region", 20, 20, 100, 100)
    mg.create_city(
        point_collection=city_points,
        center_point=(60, 60),
        size=40,
        player_id=PlayerId.ONE,
        gate_type=GateType.CITY_GATE,
    )

    # Forest clusters in the corners
    corners = [(5, 5), (5, 105), (105, 5), (105, 105)]
    for i, (cx, cy) in enumerate(corners):
        forest_points = make_region(mg, f"forest_{i}", cx - 8, cy - 8, cx + 8, cy + 8)
        mg.create_oak_forest(
            point_collection=forest_points,
            groups_density=0.08,
            group_size=8,
            clumping=3,
        )

    mg.write_map_and_save("city_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/city_example.aoe2scenario")


if __name__ == "__main__":
    main()
