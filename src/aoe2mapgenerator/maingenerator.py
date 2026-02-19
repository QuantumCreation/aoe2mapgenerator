"""Quick-start entry point for the aoe2mapgenerator library.

This module demonstrates the canonical way to use MapManager to build and
save an AoE2 scenario file.  Run it directly or use it as a copy-paste
reference for custom scripts:

    poetry run python -m aoe2mapgenerator.maingenerator

The map is written to the directory configured by ``BASE_SCENE_DIR_** ``
constants in ``common/constants/constants.py``.
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceGroupsConfig,
    VoronoiGeneratorConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


def build_example_map(map_size: int = 80) -> MapManager:
    """Build a small example map and return the MapManager.

    Args:
        map_size: Edge length of the square map in tiles (default 80).

    Returns:
        Populated ``MapManager`` ready to call ``write_map_and_save()`` on.
    """
    mm = MapManager(map_size=map_size)

    # 1. Voronoi regions on the ZONE layer
    all_points = PointCollection()
    for x in range(map_size):
        for y in range(map_size):
            all_points.add_point((x, y))

    mm.place_voronoi_zones(
        VoronoiGeneratorConfig(
            point_collection=all_points.copy(),
            interpoint_distance=20,
            map_layer_type=MapLayerType.ZONE,
        )
    )

    # 2. Oak forest in the top-left quadrant
    forest_points = PointCollection()
    for x in range(map_size // 2):
        for y in range(map_size // 2):
            forest_points.add_point((x, y))

    mm.create_oak_forest(forest_points, groups_density=0.02, group_size=8, clumping=4)

    return mm


if __name__ == "__main__":
    mm = build_example_map()
    mm.write_map_and_save("example_map.aoe2scenario")
    print("Example map written.")
