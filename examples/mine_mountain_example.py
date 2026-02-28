"""
mine_mountain_example.py
========================
Demonstrates the MINE and MOUNTAIN templates to create resource-rich highlands,
then places player forts near the mines.

Run:
    poetry run python examples/mine_mountain_example.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig, GateType
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, cx: int, cy: int, half: int):
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
    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=5)

    # Base terrain
    all_pts = make_region(mg, "all", SIZE // 2, SIZE // 2, SIZE // 2)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_pts,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_1,
        groups_density=1.0,
        group_size=1,
    ))

    # Central mountain range
    mountain_pts = make_region(mg, "mountain", 60, 60, 18)
    mg.create_mountain(point_collection=mountain_pts, max_elevation=5)

    # Gold mine in the north-west
    mine_nw = make_region(mg, "mine_nw", 25, 25, 10)
    mg.create_mine(point_collection=mine_nw, resource="GOLD", num_piles=4)

    # Stone mine in the south-east
    mine_se = make_region(mg, "mine_se", 95, 95, 10)
    mg.create_mine(point_collection=mine_se, resource="STONE", num_piles=4)

    # Player 1 fort near north-west mine
    fort1_pts = make_region(mg, "fort1", 35, 35, 25)
    mg.create_fort(
        point_collection=fort1_pts,
        center_point=(35, 35),
        size=18,
        player_id=PlayerId.ONE,
        gate_type=GateType.FORTIFIED_GATE,
    )

    # Player 2 fort near south-east mine
    fort2_pts = make_region(mg, "fort2", 85, 85, 25)
    mg.create_fort(
        point_collection=fort2_pts,
        center_point=(85, 85),
        size=18,
        player_id=PlayerId.TWO,
        gate_type=GateType.FORTIFIED_GATE,
    )

    mg.write_map_and_save("mine_mountain_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/mine_mountain_example.aoe2scenario")


if __name__ == "__main__":
    main()
