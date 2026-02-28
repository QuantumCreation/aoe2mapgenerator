"""
basic_map.py
============
Minimal end-to-end example: create a small map, fill it with grass terrain,
place a few units, and write the result to a .aoe2scenario file.

Run:
    poetry run python examples/basic_map.py
"""

from aoe2mapgenerator import MapManager, MapLayerType, PlaceGroupsConfig
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def make_region(mg: MapManager, name: str, x0: int, y0: int, x1: int, y1: int):
    """Helper: register a rectangular tile region as a named PointCollection."""
    mg.point_manager.add_point_collection(name)
    pc = mg.point_manager.get_point_collection(name)
    pc.add_points([(x, y) for x in range(x0, x1) for y in range(y0, y1)])
    return pc


def main() -> None:
    SIZE = 80

    # 1. Create an 80×80 map with a fixed seed for reproducibility.
    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=1)

    # 2. Fill the entire terrain layer with grass.
    all_points = make_region(mg, "all", 0, 0, SIZE, SIZE)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=all_points,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.GRASS_1,
        groups_density=1.0,
        group_size=1,
    ))

    # 3. Place a small cluster of militia near the centre.
    centre = make_region(mg, "centre", 35, 35, 45, 45)
    mg.place_groups(PlaceGroupsConfig(
        point_collection=centre,
        map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.MILITIA,
        player_id=PlayerId.ONE,
        groups=3,
        group_size=3,
        clumping=2,
    ))

    # 4. Write the scenario file.
    mg.write_map_and_save("basic_map.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/basic_map.aoe2scenario")


if __name__ == "__main__":
    main()
