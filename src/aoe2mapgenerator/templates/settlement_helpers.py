"""Shared helpers for settlement-type templates (FORT, VILLAGE).

Both templates place the same cluster of units (castle + knights + archers +
militia) around a central point.  This module extracts that logic so it can be
reused without duplication.
"""

from typing import Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceGroupsConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


def place_castle_and_garrison(
    map_manager,
    point_collection: PointCollection,
    center_point: Tuple[int, int],
    radius: float,
    player_id: PlayerId = PlayerId.ONE,
) -> PointCollection:
    """Place a castle at *center_point* and rings of garrison units around it.

    Placed units (innermost → outermost):
    - Castle  (at center)
    - Militia (within 0.6 × radius)
    - Archers (within 0.8 × radius)
    - Knights (within 1.0 × radius)

    Args:
        map_manager: The ``MapManager`` (or any ``IMapManager``-compatible) instance.
        point_collection: Available candidate tiles.
        center_point: Centre tile for the settlement.
        radius: Bounding radius for unit placement.
        player_id: Player who owns the settlement.

    Returns:
        The innermost ``PointCollection`` used for militia placement.
    """
    # Place a castle at the centre.
    castle_config = PlaceClosestToPointConfig(
        point_collection=point_collection,
        map_layer_type=MapLayerType.UNIT,
        obj_type=BuildingInfo.CASTLE,
        starting_point=center_point,
        player_id=player_id,
        margin=0,
    )
    map_manager.base_placer.place_closest_to_point(castle_config)

    # Knights — outermost ring
    knight_collection = point_collection.copy()
    knight_collection.filter_by_distance(center_point, distance=radius, edit_in_place=True)
    map_manager.group_placer.place_groups(
        PlaceGroupsConfig(
            point_collection=knight_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=UnitInfo.KNIGHT,
            player_id=player_id,
            groups=10,
            group_size=12,
            clumping=5,
        )
    )

    # Archers — middle ring
    archer_collection = knight_collection.copy()
    archer_collection.filter_by_distance(
        center_point, distance=radius * 0.8, edit_in_place=True
    )
    map_manager.group_placer.place_groups(
        PlaceGroupsConfig(
            point_collection=archer_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=UnitInfo.ARCHER,
            player_id=player_id,
            groups=8,
            group_size=10,
            clumping=4,
        )
    )

    # Militia — innermost ring
    militia_collection = archer_collection.copy()
    militia_collection.filter_by_distance(
        center_point, distance=radius * 0.6, edit_in_place=True
    )
    map_manager.group_placer.place_groups(
        PlaceGroupsConfig(
            point_collection=militia_collection,
            map_layer_type=MapLayerType.UNIT,
            object_type=UnitInfo.MILITIA,
            player_id=player_id,
            groups=5,
            group_size=15,
            clumping=3,
        )
    )

    return militia_collection
