"""Palace template: fortified royal compound with moat, gardens, and elite guard."""

from __future__ import annotations

import math
from typing import List, Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.gate_utility import AdvancedWallPlacer
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceGroupsConfig,
    PlaceIfPossibleConfig,
    PlacePathConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.units.wallgenerators.fort_shapes import FortShape, build_fort_shape

Point = Tuple[int, int]


def _distance_sq(a: Point, b: Point) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def _subset_annulus(
    point_collection: PointCollection,
    center: Point,
    inner_radius: float,
    outer_radius: float,
) -> PointCollection:
    inner_sq = inner_radius * inner_radius
    outer_sq = outer_radius * outer_radius
    coll = PointCollection()
    for point in point_collection.get_point_list():
        d_sq = _distance_sq(point, center)
        if inner_sq <= d_sq <= outer_sq:
            coll.add_point(point)
    return coll


def _subset_circle(
    point_collection: PointCollection,
    center: Point,
    radius: float,
) -> PointCollection:
    radius_sq = radius * radius
    coll = PointCollection()
    for point in point_collection.get_point_list():
        if _distance_sq(point, center) <= radius_sq:
            coll.add_point(point)
    return coll


def _place_moat(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center: Point,
    radius: float,
) -> None:
    shallow_ring = _subset_annulus(point_collection, center, radius + 1.0, radius + 3.0)
    deep_ring = _subset_annulus(point_collection, center, radius + 3.0, radius + 5.5)

    for ring, terrain in ((shallow_ring, TerrainId.SHALLOWS), (deep_ring, TerrainId.WATER_DEEP)):
        for point in ring.get_point_list():
            map_manager.base_placer.place_if_possible(
                PlaceIfPossibleConfig(
                    point_collection=ring,
                    map_layer_type=MapLayerType.TERRAIN,
                    obj_type=terrain,
                    starting_point=point,
                    player_id=PlayerId.GAIA,
                )
            )


def _place_palace_paths(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center: Point,
    gate_points: List[Point],
    player_id: PlayerId,
) -> None:
    cx, cy = center
    for gate in gate_points:
        map_manager.path_placer.create_path(
            PlacePathConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.ROAD,
                player_id=player_id,
                key_points=[center, gate],
                num_divisions=[2],
                random_shift_range=[1],
            )
        )

    # Cross-shaped formal path in the central garden.
    offsets = [(-8, 0), (8, 0), (0, -8), (0, 8)]
    for ox, oy in offsets:
        target = (cx + ox, cy + oy)
        map_manager.path_placer.create_path(
            PlacePathConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.ROAD,
                player_id=player_id,
                key_points=[center, target],
                num_divisions=[1],
                random_shift_range=[0],
            )
        )


def _place_palace_gardens(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center: Point,
) -> None:
    garden = _subset_circle(point_collection, center, radius=14)
    for obj, groups, size, layer in [
        (OtherInfo.FLOWERS_1, 4, 4, MapLayerType.DECOR),
        (OtherInfo.FLOWERS_2, 4, 4, MapLayerType.DECOR),
        (OtherInfo.FLOWER_BED, 3, 3, MapLayerType.DECOR),
        (OtherInfo.PLANT_FLOWERS, 3, 3, MapLayerType.DECOR),
        (OtherInfo.BUSH_A, 3, 3, MapLayerType.DECOR),
        (OtherInfo.BUSH_B, 3, 3, MapLayerType.DECOR),
        (OtherInfo.TREE_CYPRESS, 4, 2, MapLayerType.UNIT),
        (OtherInfo.TREE_ITALIAN_PINE, 4, 2, MapLayerType.UNIT),
        (OtherInfo.STATUE_COLUMN, 2, 1, MapLayerType.DECOR),
        (OtherInfo.WELL, 1, 1, MapLayerType.DECOR),
    ]:
        map_manager.group_placer.place_groups(
            PlaceGroupsConfig(
                point_collection=garden.copy(),
                map_layer_type=layer,
                object_type=obj,
                player_id=PlayerId.GAIA,
                groups=groups,
                group_size=size,
                clumping=5,
            )
        )


def _place_royal_garrison(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center: Point,
    player_id: PlayerId,
) -> None:
    inner = _subset_circle(point_collection, center, radius=12)
    elite_mix = [
        (UnitInfo.PALADIN, 3, 3),
        (UnitInfo.CHAMPION, 3, 4),
        (UnitInfo.HALBERDIER, 2, 4),
        (UnitInfo.ARBALESTER, 3, 3),
        (UnitInfo.HAND_CANNONEER, 2, 3),
        (UnitInfo.MONK, 1, 2),
    ]
    for unit, groups, size in elite_mix:
        map_manager.group_placer.place_groups(
            PlaceGroupsConfig(
                point_collection=inner.copy(),
                map_layer_type=MapLayerType.UNIT,
                object_type=unit,
                player_id=player_id,
                groups=groups,
                group_size=size,
                clumping=4,
            )
        )


@register_template(TemplateType.PALACE)
class PalaceTemplate(AbstractTemplate):
    """Generates a royal palace district with a defensive shell and gardens."""

    def __init__(self, name: str = "Palace", description: str = "Creates a fortified palace"):
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        center_point: Point = kwargs.get(
            "center_point",
            point_collection.get_average_point_position(),
        )
        radius: int = kwargs.get("radius", kwargs.get("size", 22))
        player_id: PlayerId = kwargs.get("player_id", PlayerId.ONE)
        gate_type: GateType = kwargs.get("gate_type", GateType.FORTIFIED_GATE)
        include_moat: bool = kwargs.get("include_moat", True)

        fort_shape: FortShape = build_fort_shape("square", center_point, half_size=radius)
        wall_points = fort_shape.wall_points
        corner_points = fort_shape.corner_points
        gate_points = fort_shape.gate_points
        interior = _subset_circle(point_collection, center_point, radius=radius - 2)

        wall_placer = AdvancedWallPlacer(map_manager.get_map())
        wall_type = gate_type.get_building_info_wall()

        wall_placer.place_wall_points(
            map_manager,
            point_collection,
            wall_points,
            wall_type,
            player_id,
        )
        map_manager.gate_placer.place_gate_on_four_sides(
            point_collection=point_collection.copy(),
            map_layer_type=MapLayerType.UNIT,
            gate_type=gate_type,
            player_id=player_id,
        )

        for corner in corner_points:
            map_manager.base_placer.place_closest_to_point(
                PlaceClosestToPointConfig(
                    point_collection=point_collection.copy(),
                    map_layer_type=MapLayerType.UNIT,
                    obj_type=BuildingInfo.GUARD_TOWER,
                    starting_point=corner,
                    player_id=player_id,
                    margin=1,
                )
            )

        if include_moat:
            _place_moat(map_manager, point_collection, center_point, float(radius))

        _place_palace_paths(map_manager, interior, center_point, gate_points, player_id)
        _place_palace_gardens(map_manager, interior, center_point)
        _place_royal_garrison(map_manager, interior, center_point, player_id)

        # Place the keep at the end so decorative/random passes never displace it.
        map_manager.base_placer.place_closest_to_point(
            PlaceClosestToPointConfig(
                point_collection=interior.copy(),
                map_layer_type=MapLayerType.UNIT,
                obj_type=BuildingInfo.CASTLE,
                starting_point=center_point,
                player_id=player_id,
                margin=1,
            )
        )

        return interior
