"""
castle_road_example.py
======================
Places two opponent castles connected by a central road, with stone walls
protecting each keep.

Run:
    poetry run python examples/castle_road_example.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig, GateType, PointCollection
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, cx: int, cy: int, half: int) -> PointCollection:
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
    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=11)

    # Base terrain
    all_pts = make_region(mg, "all", SIZE // 2, SIZE // 2, SIZE // 2)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_pts,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_1,
        groups_density=1.0,
        group_size=1,
    ))

    # Castle 1 (player 1) — west side
    castle1_pts = make_region(mg, "castle1", 25, 60, 20)
    mg.create_castle(
        point_collection=castle1_pts,
        center_point=(25, 60),
        player_id=PlayerId.ONE,
        gate_type=GateType.STONE_GATE,
    )

    # Castle 2 (player 2) — east side
    castle2_pts = make_region(mg, "castle2", 95, 60, 20)
    mg.create_castle(
        point_collection=castle2_pts,
        center_point=(95, 60),
        player_id=PlayerId.TWO,
        gate_type=GateType.STONE_GATE,
    )

    # Road connecting the two castles through the centre
    road_pts = make_region(mg, "road", 60, 60, 40)
    mg.create_road(
        point_collection=road_pts,
        key_points=[(25, 60), (60, 60), (95, 60)],
        width=3,
    )

    # Flanking walls for each castle
    walls1_pts = make_region(mg, "walls1", 25, 60, 22)
    mg.create_walls(
        point_collection=walls1_pts,
        gate_type=GateType.STONE_GATE,
        border_width=1,
        player_id=PlayerId.ONE,
    )

    walls2_pts = make_region(mg, "walls2", 95, 60, 22)
    mg.create_walls(
        point_collection=walls2_pts,
        gate_type=GateType.STONE_GATE,
        border_width=1,
        player_id=PlayerId.TWO,
    )

    mg.write_map_and_save("castle_road_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/castle_road_example.aoe2scenario")


if __name__ == "__main__":
    main()
