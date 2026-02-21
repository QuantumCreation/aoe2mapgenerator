"""Shared helpers used by settlement-type templates (FORT, VILLAGE).

Public surface
--------------
Fort
  - place_fort_interior     — castle, paths, gate guards, buildings, troops
  - place_fort_decorations  — gaia decor outside walls (trees, bushes, pikes…)
Village
  - place_village_interior  — town centre, farms, resources, villagers, troops

Legacy (kept for backward-compat):
  - place_castle_and_garrison — original simple village helper
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceGroupsConfig,
    PlacePathConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection

# ---------------------------------------------------------------------------
# Private utilities
# ---------------------------------------------------------------------------


def _place_building_at_angle(
    map_manager: IMapManager,
    point_collection: PointCollection,
    cx: int,
    cy: int,
    dist: float,
    angle_rad: float,
    building_type: BuildingInfo,
    player_id: PlayerId,
    margin: int = 1,
) -> None:
    """Place *building_type* at the polar position (*dist*, *angle_rad*) from (*cx*, *cy*)."""
    target = (int(cx + dist * math.cos(angle_rad)), int(cy + dist * math.sin(angle_rad)))
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=point_collection.copy(),
            map_layer_type=MapLayerType.UNIT,
            obj_type=building_type,
            starting_point=target,
            player_id=player_id,
            margin=margin,
        )
    )


def _place_gaia_cluster_at_angle(
    map_manager: IMapManager,
    point_collection: PointCollection,
    cx: int,
    cy: int,
    dist: float,
    angle_rad: float,
    obj_type: AOE2ObjectType,
    groups: int = 1,
    group_size: int = 1,
    clumping: int = 3,
) -> None:
    """Place a gaia *obj_type* cluster at the polar offset (*dist*, *angle_rad*)."""
    target = (int(cx + dist * math.cos(angle_rad)), int(cy + dist * math.sin(angle_rad)))
    coll = point_collection.copy()
    coll.filter_by_distance(target, distance=max(group_size + 2, 5), edit_in_place=True)
    map_manager.group_placer.place_groups(
        PlaceGroupsConfig(
            point_collection=coll,
            map_layer_type=MapLayerType.UNIT,
            object_type=obj_type,
            player_id=PlayerId.GAIA,
            groups=groups,
            group_size=group_size,
            clumping=clumping,
            start_point=target,
        )
    )


def _place_unit_cluster_at_angle(
    map_manager: IMapManager,
    point_collection: PointCollection,
    cx: int,
    cy: int,
    dist: float,
    angle_rad: float,
    obj_type: UnitInfo,
    player_id: PlayerId,
    groups: int = 1,
    group_size: int = 2,
    clumping: int = 3,
) -> None:
    """Place a unit cluster at the polar offset (*dist*, *angle_rad*)."""
    target = (int(cx + dist * math.cos(angle_rad)), int(cy + dist * math.sin(angle_rad)))
    coll = point_collection.copy()
    coll.filter_by_distance(target, distance=max(group_size + 3, 6), edit_in_place=True)
    map_manager.group_placer.place_groups(
        PlaceGroupsConfig(
            point_collection=coll,
            map_layer_type=MapLayerType.UNIT,
            object_type=obj_type,
            player_id=player_id,
            groups=groups,
            group_size=group_size,
            clumping=clumping,
            start_point=target,
        )
    )


# ---------------------------------------------------------------------------
# Fort helpers
# ---------------------------------------------------------------------------


def place_fort_interior(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center_point: Tuple[int, int],
    radius: float,
    gate_positions: List[Tuple[int, int]],
    player_id: PlayerId = PlayerId.ONE,
) -> PointCollection:
    """Furnish the inside of a walled fort.

    Call this *after* the perimeter walls have been placed.

    1. Castle at the fort centre.
    2. Road paths — one dirt-road segment per gate leading to the castle.
    3. Gate guards — 2 Spearmen posted just inside every gate.
    4. Military buildings — Barracks at NE/SW, Archery Ranges at NW/SE.
    5. Concentric troop rings: Spearmen (inner) → Archers (mid) → Knights (outer).

    Args:
        map_manager: Active ``IMapManager`` instance.
        point_collection: Candidate tiles inside the fort.
        center_point: Central tile; castle is placed here.
        radius: Effective interior radius (distance from centre to gate wall).
        gate_positions: List of ``(x, y)`` gate midpoints used for paths and guards.
        player_id: Owning player.

    Returns:
        Inner ``PointCollection`` (spearman zone) for downstream chaining.
    """
    cx, cy = center_point

    # 1. Castle at centre ---------------------------------------------------
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=point_collection,
            map_layer_type=MapLayerType.UNIT,
            obj_type=BuildingInfo.CASTLE,
            starting_point=center_point,
            player_id=player_id,
            margin=0,
        )
    )

    # 2. Road paths from every gate to the castle ---------------------------
    for gate_pos in gate_positions:
        map_manager.path_placer.create_path(
            PlacePathConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.ROAD,
                player_id=player_id,
                key_points=[gate_pos, center_point],
                num_divisions=[2],
                random_shift_range=[1],
            )
        )

    # 3. Gate guards — 2 Spearmen just inside each gate --------------------
    for gate_pos in gate_positions:
        guard_coll = point_collection.copy()
        guard_coll.filter_by_distance(gate_pos, distance=3, edit_in_place=True)
        map_manager.group_placer.place_groups(
            PlaceGroupsConfig(
                point_collection=guard_coll,
                map_layer_type=MapLayerType.UNIT,
                object_type=UnitInfo.SPEARMAN,
                player_id=player_id,
                groups=1,
                group_size=2,
                clumping=2,
            )
        )

    # 4. Military production buildings at ~60 % radius ---------------------
    bldg_r = radius * 0.60
    _place_building_at_angle(map_manager, point_collection, cx, cy, bldg_r, math.radians(45),  BuildingInfo.BARRACKS,      player_id)
    _place_building_at_angle(map_manager, point_collection, cx, cy, bldg_r, math.radians(225), BuildingInfo.BARRACKS,      player_id)
    _place_building_at_angle(map_manager, point_collection, cx, cy, bldg_r, math.radians(135), BuildingInfo.ARCHERY_RANGE, player_id)
    _place_building_at_angle(map_manager, point_collection, cx, cy, bldg_r, math.radians(315), BuildingInfo.ARCHERY_RANGE, player_id)

    # 5. Concentric troop rings --------------------------------------------
    inner_coll = point_collection.copy()
    inner_coll.filter_by_distance(center_point, distance=radius * 0.40, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=inner_coll, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.SPEARMAN, player_id=player_id,
        groups=4, group_size=5, clumping=3,
    ))

    mid_coll = point_collection.copy()
    mid_coll.filter_by_distance(center_point, distance=radius * 0.65, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=mid_coll, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.ARCHER, player_id=player_id,
        groups=5, group_size=8, clumping=4,
    ))

    outer_coll = point_collection.copy()
    outer_coll.filter_by_distance(center_point, distance=radius * 0.85, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=outer_coll, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.KNIGHT, player_id=player_id,
        groups=6, group_size=10, clumping=4,
    ))

    return inner_coll


def place_fort_decorations(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center_point: Tuple[int, int],
    radius: float,
    gate_positions: List[Tuple[int, int]],
) -> None:
    """Place gaia decorations outside the fort walls.

    Decorations (all ``PlayerId.GAIA``):

    - *Impaled corpses* just outside every gate — grisly gatehouse warning.
    - *Oak trees* in 4 clusters at the diagonal corners (~45 ° offsets).
    - *Bush / shrub* splashes near the diagonal curtain walls.
    - *Rocks* scattered around the outer perimeter.
    - *Flowers* near the gate approach roads.
    - *Stump* details near tree clusters.

    Args:
        map_manager: Active ``IMapManager`` instance.
        point_collection: Full-map candidate tiles (includes exterior).
        center_point: Fort centre.
        radius: Effective fort radius (gate-wall distance from centre).
        gate_positions: Cardinal gate midpoints for impaled corpse placement.
    """
    cx, cy = center_point
    outer = radius + 5   # just outside the wall

    # Impaled corpse / head on a pike just outside each gate ---------------
    for gate_pos in gate_positions:
        gx, gy = gate_pos
        # Direction vector from centre to gate — step 3 tiles outward
        dx = gx - cx
        dy = gy - cy
        dist = math.sqrt(dx * dx + dy * dy) or 1
        spike_pt = (int(gx + 3 * dx / dist), int(gy + 3 * dy / dist))
        map_manager.base_placer.place_closest_to_point(
            PlaceClosestToPointConfig(
                point_collection=point_collection.copy(),
                map_layer_type=MapLayerType.UNIT,
                obj_type=OtherInfo.IMPALED_CORPSE,
                starting_point=spike_pt,
                player_id=PlayerId.GAIA,
                margin=0,
            )
        )

    # Oak tree clusters at the 4 diagonal corners of the fort --------------
    tree_types = [OtherInfo.TREE_OAK, OtherInfo.TREE_OAK_FOREST, OtherInfo.TREE_A, OtherInfo.TREE_B]
    for i, angle_deg in enumerate([45, 135, 225, 315]):
        tree_type = tree_types[i % len(tree_types)]
        _place_gaia_cluster_at_angle(
            map_manager, point_collection, cx, cy,
            dist=outer + 3,
            angle_rad=math.radians(angle_deg),
            obj_type=tree_type,
            groups=1, group_size=6, clumping=4,
        )

    # Scattered bush / shrub near curtain walls ----------------------------
    bush_types = [OtherInfo.BUSH_A, OtherInfo.BUSH_B, OtherInfo.BUSH_C, OtherInfo.PLANT_BUSH_GREEN]
    for i, angle_deg in enumerate([45, 90, 135, 180, 225, 270, 315, 0]):
        btype = bush_types[i % len(bush_types)]
        _place_gaia_cluster_at_angle(
            map_manager, point_collection, cx, cy,
            dist=outer + random.randint(1, 4),
            angle_rad=math.radians(angle_deg + random.randint(-12, 12)),
            obj_type=btype,
            groups=1, group_size=2, clumping=2,
        )

    # Rock scatter around outer perimeter ----------------------------------
    for angle_deg in [30, 75, 150, 200, 260, 330]:
        rock = random.choice([OtherInfo.ROCK_1, OtherInfo.ROCK_2])
        _place_gaia_cluster_at_angle(
            map_manager, point_collection, cx, cy,
            dist=outer + random.randint(2, 6),
            angle_rad=math.radians(angle_deg),
            obj_type=rock,
            groups=1, group_size=1, clumping=1,
        )

    # Flowers near gate approach roads ------------------------------------
    for gate_pos in gate_positions:
        gx, gy = gate_pos
        flower = random.choice([OtherInfo.FLOWERS_1, OtherInfo.FLOWERS_2,
                                 OtherInfo.FLOWERS_3, OtherInfo.FLOWERS_4])
        _place_gaia_cluster_at_angle(
            map_manager, point_collection, cx, cy,
            dist=math.sqrt((gx - cx) ** 2 + (gy - cy) ** 2) + 4,
            angle_rad=math.atan2(gy - cy, gx - cx) + math.radians(random.randint(-20, 20)),
            obj_type=flower,
            groups=1, group_size=3, clumping=2,
        )


# ---------------------------------------------------------------------------
# Village interior
# ---------------------------------------------------------------------------


def place_village_interior(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center_point: Tuple[int, int],
    radius: float,
    player_id: PlayerId = PlayerId.ONE,
) -> PointCollection:
    """Place a complete living village settlement.

    Layout (from centre outward):

    1. **Town Center** at the village centre.
    2. **Mill + Farms** — mill NW of centre, 6 farms clustered around it.
    3. **Barracks** — SE of centre.
    4. **Watch Towers** — two towers near the village edge at ~NE and NW.
    5. **Gaia resources** — stone mine, gold mine, forage bushes, deer, sheep.
    6. **Pond** — small ``SHALLOWS`` terrain splash SW of centre.
    7. *Tree clusters* — 3 splashes at diagonal offsets (30–70 % radius).
    8. **Paths** — dirt roads connecting Town Center to Mill, Barracks,
       the edge in all 4 cardinal directions.
    9. **Troops** — Spearmen/Man-at-arms inside; Archers near the village edge.
    10. **Villagers** — male/female workers in various tasks.

    Args:
        map_manager: Active ``IMapManager`` instance.
        point_collection: Candidate tiles for the village area.
        center_point: Central tile; Town Center is placed here.
        radius: Bounding radius for the entire village.
        player_id: Owning player.

    Returns:
        Inner ``PointCollection`` (town-center zone) for downstream chaining.
    """
    cx, cy = center_point
    R = radius

    # 1. Town Center -------------------------------------------------------
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=point_collection,
            map_layer_type=MapLayerType.UNIT,
            obj_type=BuildingInfo.TOWN_CENTER,
            starting_point=center_point,
            player_id=player_id,
            margin=0,
        )
    )

    # 2. Mill (NW) + 6 Farms around it ------------------------------------
    mill_pt = (int(cx - R * 0.45), int(cy - R * 0.30))
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=point_collection,
            map_layer_type=MapLayerType.UNIT,
            obj_type=BuildingInfo.MILL,
            starting_point=mill_pt,
            player_id=player_id,
            margin=1,
        )
    )
    farm_coll = point_collection.copy()
    farm_coll.filter_by_distance(mill_pt, distance=10, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=farm_coll, map_layer_type=MapLayerType.UNIT,
        object_type=BuildingInfo.FARM, player_id=player_id,
        groups=6, group_size=1, clumping=5,
    ))

    # 3. Barracks (SE) ---------------------------------------------------
    _place_building_at_angle(map_manager, point_collection, cx, cy,
                              R * 0.50, math.radians(135), BuildingInfo.BARRACKS, player_id)

    # 4. Watch Towers near edge at NE and NW ------------------------------
    _place_building_at_angle(map_manager, point_collection, cx, cy,
                              R * 0.78, math.radians(315), BuildingInfo.WATCH_TOWER, player_id)
    _place_building_at_angle(map_manager, point_collection, cx, cy,
                              R * 0.78, math.radians(225), BuildingInfo.WATCH_TOWER, player_id)

    # 5. Gaia resources ---------------------------------------------------
    # Stone mine — NE far
    _place_gaia_cluster_at_angle(map_manager, point_collection, cx, cy,
                                  R * 0.70, math.radians(45),
                                  OtherInfo.STONE_MINE, groups=1, group_size=2, clumping=3)
    # Gold mine — SW far
    _place_gaia_cluster_at_angle(map_manager, point_collection, cx, cy,
                                  R * 0.68, math.radians(270),
                                  OtherInfo.GOLD_MINE, groups=1, group_size=2, clumping=3)
    # Forage bushes — W mid
    _place_gaia_cluster_at_angle(map_manager, point_collection, cx, cy,
                                  R * 0.45, math.radians(180),
                                  OtherInfo.FORAGE_BUSH, groups=1, group_size=4, clumping=4)
    # Fruit bushes — bonus near edge
    _place_gaia_cluster_at_angle(map_manager, point_collection, cx, cy,
                                  R * 0.60, math.radians(200),
                                  OtherInfo.FRUIT_BUSH, groups=1, group_size=3, clumping=3)
    # Deer herd — E
    _place_gaia_cluster_at_angle(map_manager, point_collection, cx, cy,
                                  R * 0.65, math.radians(0),
                                  UnitInfo.DEER, groups=1, group_size=4, clumping=3)
    # Sheep — S (near shepherd villager)
    _place_gaia_cluster_at_angle(map_manager, point_collection, cx, cy,
                                  R * 0.35, math.radians(90),
                                  UnitInfo.SHEEP, groups=1, group_size=4, clumping=3)

    # 6. Pond — SHALLOWS terrain circle SW -------------------------------
    pond_pt = (int(cx - R * 0.50), int(cy + R * 0.55))
    pond_coll = point_collection.copy()
    pond_coll.filter_by_distance(pond_pt, distance=5, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=pond_coll, map_layer_type=MapLayerType.TERRAIN,
        object_type=TerrainId.SHALLOWS, player_id=PlayerId.GAIA,
        groups=1, group_size=18, clumping=4, start_point=pond_pt,
    ))

    # 7. Tree clusters at random diagonal offsets -------------------------
    tree_choices = [OtherInfo.TREE_OAK, OtherInfo.TREE_A, OtherInfo.TREE_B]
    for i, (angle_deg, dist_frac) in enumerate([(340, 0.55), (60, 0.65), (160, 0.60)]):
        _place_gaia_cluster_at_angle(
            map_manager, point_collection, cx, cy,
            dist=R * dist_frac, angle_rad=math.radians(angle_deg),
            obj_type=tree_choices[i % len(tree_choices)],
            groups=1, group_size=7, clumping=5,
        )

    # 8. Paths: centre → mill, barracks, N, S, E, W edges ----------------
    barracks_pt = (int(cx + R * 0.50 * math.cos(math.radians(135))),
                   int(cy + R * 0.50 * math.sin(math.radians(135))))
    # Centre → Mill
    map_manager.path_placer.create_path(PlacePathConfig(
        point_collection=point_collection.copy(),
        map_layer_type=MapLayerType.TERRAIN, obj_type=TerrainId.DIRT_1,
        player_id=player_id,
        key_points=[center_point, mill_pt],
        num_divisions=[2], random_shift_range=[2],
    ))
    # Centre → Barracks
    map_manager.path_placer.create_path(PlacePathConfig(
        point_collection=point_collection.copy(),
        map_layer_type=MapLayerType.TERRAIN, obj_type=TerrainId.DIRT_1,
        player_id=player_id,
        key_points=[center_point, barracks_pt],
        num_divisions=[2], random_shift_range=[2],
    ))
    # Paths to 4 cardinal edges
    for angle_deg in [0, 90, 180, 270]:
        edge_pt = (int(cx + R * math.cos(math.radians(angle_deg))),
                   int(cy + R * math.sin(math.radians(angle_deg))))
        map_manager.path_placer.create_path(PlacePathConfig(
            point_collection=point_collection.copy(),
            map_layer_type=MapLayerType.TERRAIN, obj_type=TerrainId.DIRT_1,
            player_id=player_id,
            key_points=[center_point, edge_pt],
            num_divisions=[3], random_shift_range=[2],
        ))

    # 9. Military units ---------------------------------------------------
    # Spearmen inner patrol ring
    inner_coll = point_collection.copy()
    inner_coll.filter_by_distance(center_point, distance=R * 0.35, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=inner_coll, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.SPEARMAN, player_id=player_id,
        groups=3, group_size=3, clumping=3,
    ))
    # Man-at-arms wandering mid ring
    mid_coll = point_collection.copy()
    mid_coll.filter_by_distance(center_point, distance=R * 0.60, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=mid_coll, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.MAN_AT_ARMS, player_id=player_id,
        groups=2, group_size=3, clumping=4,
    ))
    # Archers near edge
    outer_coll = point_collection.copy()
    outer_coll.filter_by_distance(center_point, distance=R * 0.90, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=outer_coll, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.ARCHER, player_id=player_id,
        groups=4, group_size=4, clumping=5,
    ))

    # 10. Villagers -------------------------------------------------------
    villager_types = [
        UnitInfo.VILLAGER_MALE,
        UnitInfo.VILLAGER_FEMALE,
        UnitInfo.VILLAGER_MALE_FARMER,
        UnitInfo.VILLAGER_FEMALE_FORAGER,
        UnitInfo.VILLAGER_MALE_LUMBERJACK,
        UnitInfo.VILLAGER_FEMALE_SHEPHERD,
        UnitInfo.VILLAGER_MALE_BUILDER,
        UnitInfo.VILLAGER_FEMALE_FARMER,
    ]
    for i, vtype in enumerate(villager_types):
        angle = math.radians(i * 45 + random.randint(-15, 15))
        dist = R * random.uniform(0.15, 0.50)
        _place_unit_cluster_at_angle(
            map_manager, point_collection, cx, cy,
            dist=dist, angle_rad=angle,
            obj_type=vtype, player_id=player_id,
            groups=1, group_size=1, clumping=1,
        )

    return inner_coll


# ---------------------------------------------------------------------------
# Legacy: simple village garrison (used by the original VillageTemplate)
# ---------------------------------------------------------------------------


def place_castle_and_garrison(
    map_manager: IMapManager,
    point_collection: PointCollection,
    center_point: Tuple[int, int],
    radius: float,
    player_id: PlayerId = PlayerId.ONE,
) -> PointCollection:
    """Place a castle at *center_point* and rings of garrison units around it.

    This is the *legacy* helper kept for backward compatibility.
    New code should prefer :func:`place_village_interior`.

    Placed units (innermost → outermost):
    - Castle  (at center)
    - Militia (within 0.6 × radius)
    - Archers (within 0.8 × radius)
    - Knights (within 1.0 × radius)
    """
    map_manager.base_placer.place_closest_to_point(
        PlaceClosestToPointConfig(
            point_collection=point_collection,
            map_layer_type=MapLayerType.UNIT,
            obj_type=BuildingInfo.CASTLE,
            starting_point=center_point,
            player_id=player_id,
            margin=0,
        )
    )

    knight_collection = point_collection.copy()
    knight_collection.filter_by_distance(center_point, distance=radius, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=knight_collection, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.KNIGHT, player_id=player_id,
        groups=10, group_size=12, clumping=5,
    ))

    archer_collection = knight_collection.copy()
    archer_collection.filter_by_distance(center_point, distance=radius * 0.8, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=archer_collection, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.ARCHER, player_id=player_id,
        groups=8, group_size=10, clumping=4,
    ))

    militia_collection = archer_collection.copy()
    militia_collection.filter_by_distance(center_point, distance=radius * 0.6, edit_in_place=True)
    map_manager.group_placer.place_groups(PlaceGroupsConfig(
        point_collection=militia_collection, map_layer_type=MapLayerType.UNIT,
        object_type=UnitInfo.MILITIA, player_id=player_id,
        groups=5, group_size=15, clumping=3,
    ))

    return militia_collection
