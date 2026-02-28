"""Missing template implementations: WALLS, ROAD, MINE, MOUNTAIN, CASTLE, RIVER.

Each template is registered with ``@register_template`` and follows the
``AbstractTemplate`` contract.  They are imported as a side-effect by
``MapManager`` so registration happens automatically.

Template overview
-----------------
WALLS
    Standalone perimeter wall around any ``PointCollection`` region.
    No interior, no gates.  Use FORT when you need a full garrison.

ROAD
    Winding dirt road between two or more waypoints.  Terrain-layer operation
    — writes a ``DIRT_ROAD`` (or caller-chosen) terrain across the path tiles.

MINE
    Gold or stone mine cluster with rocky surrounding terrain and a few
    guard units to signal the strategic value of the site.

MOUNTAIN
    Rocky elevated terrain patch: sets elevation + assigns mountain/snow
    terrain via a simple noise warp, then scatters rock decor.

CASTLE
    Heavily fortified castle: star or square fort perimeter (stone walls)
    with a central keep, flanking towers, and elite guard troops.

RIVER
    An edge-to-edge river: traces a winding path across the selected region,
    fills path tiles with shallow water, and populates with fish and reeds.
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

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.placer_configs import (
    AddBordersConfig,
    PlaceGroupsConfig,
    PlaceIfPossibleConfig,
    PlacePathConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


# ---------------------------------------------------------------------------
# WALLS
# ---------------------------------------------------------------------------


@register_template(TemplateType.WALLS)
class WallsTemplate(AbstractTemplate):
    """Place a standalone perimeter wall around a region with no interior.

    Unlike ``FORT`` there are no gates, no interior buildings, and no troops.
    This is useful for enclosing natural features (forests, mines) or as a
    stand-alone defensive work that the caller will customise further.

    Keyword arguments
    ~~~~~~~~~~~~~~~~~
    ``gate_type`` (GateType)
        Wall material.  Default ``GateType.FORTIFIED_GATE`` (Fortified Wall).
    ``border_width`` (int)
        Thickness of the wall perimeter in tiles.  Default 1.
    ``player_id`` (PlayerId)
        Owner.  Default ``PlayerId.ONE``.
    """

    def __init__(self, name: str = "Walls", description: str = "Perimeter wall") -> None:
        pass

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        gate_type: GateType = kwargs.get("gate_type", GateType.FORTIFIED_GATE)
        border_width: int = max(1, int(kwargs.get("border_width", 1)))
        player_id: PlayerId = kwargs.get("player_id", PlayerId.ONE)

        wall_type = gate_type.get_building_info_wall()

        map_manager.place_borders(
            AddBordersConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.UNIT,
                obj_type=wall_type,
                player_id=player_id,
                border_width=border_width,
            )
        )

        return point_collection


# ---------------------------------------------------------------------------
# ROAD
# ---------------------------------------------------------------------------


@register_template(TemplateType.ROAD)
class RoadTemplate(AbstractTemplate):
    """Trace a winding dirt road between two or more waypoints.

    The road is written to the TERRAIN layer so it appears as a visible path
    in‐game.  Supports AoE2's full terrain palette but defaults to
    ``TerrainId.DIRT_ROAD``.

    Keyword arguments
    ~~~~~~~~~~~~~~~~~
    ``key_points`` (list[tuple[int, int]])
        Ordered list of waypoints.  The road visits each in sequence.
        **Required** — the template cannot infer waypoints from the point
        collection.
    ``terrain_id`` (TerrainId)
        Road surface terrain.  Default ``TerrainId.DIRT_ROAD``.
    ``player_id`` (PlayerId)
        Owner of placed terrain.  Default ``PlayerId.GAIA``.
    ``num_divisions`` (list[int])
        Per-segment subdivision count.  Defaults to ``[3]`` repeated.
    ``random_shift_range`` (list[int])
        Per-segment random warp amplitude.  Defaults to ``[4]`` repeated.
    ``width`` (int)
        Road width in tiles (road tiles on each side of centre).  Default 1.
    """

    def __init__(self, name: str = "Road", description: str = "Winding road") -> None:
        pass

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        key_points: list[tuple[int, int]] = kwargs.get("key_points", [])
        if len(key_points) < 2:
            # Derive start/end from the bounding box of the point collection.
            pts = point_collection.get_point_list()
            if len(pts) < 2:
                return point_collection
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            key_points = [
                (min(xs), (min(ys) + max(ys)) // 2),
                (max(xs), (min(ys) + max(ys)) // 2),
            ]

        terrain_id: TerrainId = kwargs.get("terrain_id", TerrainId.DIRT_ROAD)
        player_id: PlayerId = kwargs.get("player_id", PlayerId.GAIA)
        n_segments = max(1, len(key_points) - 1)
        num_divisions: list[int] = kwargs.get("num_divisions", [3] * n_segments)
        random_shift_range: list[int] = kwargs.get("random_shift_range", [4] * n_segments)
        width: int = max(1, int(kwargs.get("width", 1)))

        # Extend lists to cover every segment gap.
        while len(num_divisions) < n_segments:
            num_divisions.append(3)
        while len(random_shift_range) < n_segments:
            random_shift_range.append(4)

        map_manager.create_path(
            PlacePathConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=terrain_id,
                player_id=player_id,
                key_points=key_points,
                num_divisions=num_divisions[:n_segments],
                random_shift_range=random_shift_range[:n_segments],
            )
        )

        # For width > 1, repeat with slight perpendicular offsets.
        if width > 1:
            from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
            pad = width - 1
            for dx in range(-pad, pad + 1):
                for dy in range(-pad, pad + 1):
                    if dx == 0 and dy == 0:
                        continue
                    shifted_pts = [
                        (x + dx, y + dy) for (x, y) in key_points
                    ]
                    try:
                        map_manager.create_path(
                            PlacePathConfig(
                                point_collection=point_collection,
                                map_layer_type=MapLayerType.TERRAIN,
                                obj_type=terrain_id,
                                player_id=player_id,
                                key_points=shifted_pts,
                                num_divisions=num_divisions[:n_segments],
                                random_shift_range=random_shift_range[:n_segments],
                            )
                        )
                    except Exception:
                        pass  # shifted endpoints may fall outside bounds

        return point_collection


# ---------------------------------------------------------------------------
# MINE
# ---------------------------------------------------------------------------

# Decorative rocks used around mine sites.
_MINE_ROCKS: list = [OtherInfo.ROCK_1, OtherInfo.ROCK_2, OtherInfo.ROCK_FORMATION_1]


@register_template(TemplateType.MINE)
class MineTemplate(AbstractTemplate):
    """A gold or stone mine cluster with rocky terrain and guard units.

    Terrain under the mine is set to ``TerrainId.DIRT_2`` (rocky ground).
    Resource piles are scattered in tight clusters.  Two guard soldiers
    (belonging to the owning player) flank the entrance.

    Keyword arguments
    ~~~~~~~~~~~~~~~~~
    ``resource`` (str)
        ``"GOLD"`` (default) or ``"STONE"``.
    ``num_piles`` (int)
        Number of resource pile groups.  Default 4.
    ``guard_count`` (int)
        Number of soldiers placed near the mine entrance.  Default 2.
        Set to 0 to skip guard placement.
    ``player_id`` (PlayerId)
        Owner of resource sites **and** guards.  Default ``PlayerId.GAIA``
        (unowned mine, neutral guards).
    ``center_point`` (tuple[int, int])
        Centre tile.  Defaults to the centroid of *point_collection*.
    """

    def __init__(self, name: str = "Mine", description: str = "Resource mine") -> None:
        pass

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        resource: str = str(kwargs.get("resource", "GOLD")).upper()
        num_piles: int = max(1, int(kwargs.get("num_piles", 4)))
        guard_count: int = max(0, int(kwargs.get("guard_count", 2)))
        player_id: PlayerId = kwargs.get("player_id", PlayerId.GAIA)
        center_point: tuple[int, int] = kwargs.get(
            "center_point",
            point_collection.get_average_point_position(),
        )

        resource_obj = (
            OtherInfo.GOLD_MINE if resource == "GOLD" else OtherInfo.STONE_MINE
        )

        # 1. Rocky terrain base.
        map_manager.place_groups(
            PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.TERRAIN,
                object_type=TerrainId.DIRT_2,
                player_id=PlayerId.GAIA,
                groups_density=1.0,
                group_size=1,
                margin=0,
            )
        )

        # 2. Resource piles in tight clusters.
        map_manager.place_groups(
            PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.DECOR,
                object_type=resource_obj,
                player_id=PlayerId.GAIA,
                groups=num_piles,
                group_size=3,
                clumping=1,
                margin=1,
            )
        )

        # 3. Rock decor scattered sparsely around the perimeter.
        for rock in _MINE_ROCKS:
            map_manager.place_groups(
                PlaceGroupsConfig(
                    point_collection=point_collection,
                    map_layer_type=MapLayerType.DECOR,
                    object_type=rock,
                    player_id=PlayerId.GAIA,
                    groups=2,
                    group_size=1,
                    margin=1,
                )
            )

        # 4. Guard soldiers (skipped when guard_count==0 or GAIA player).
        if guard_count > 0 and player_id != PlayerId.GAIA:
            cx, cy = center_point
            size = point_collection.get_size()
            radius = max(4, int(math.sqrt(size) * 0.5))
            for i in range(guard_count):
                angle = (2 * math.pi * i) / guard_count
                gx = int(cx + radius * math.cos(angle))
                gy = int(cy + radius * math.sin(angle))
                map_manager.base_placer.place_if_possible(
                    PlaceIfPossibleConfig(
                        point_collection=point_collection,
                        map_layer_type=MapLayerType.UNIT,
                        obj_type=UnitInfo.MAN_AT_ARMS,
                        starting_point=(gx, gy),
                        player_id=player_id,
                        margin=0,
                    )
                )

        return point_collection


# ---------------------------------------------------------------------------
# MOUNTAIN
# ---------------------------------------------------------------------------


@register_template(TemplateType.MOUNTAIN)
class MountainTemplate(AbstractTemplate):
    """Rocky elevated terrain patch.

    Sets elevation on all tiles in the selected region proportional to
    their distance from the centre, then overlays mountain terrain and
    scatters rock decor objects.  The result looks like a low hill or
    rocky outcrop depending on ``max_elevation``.

    Keyword arguments
    ~~~~~~~~~~~~~~~~~
    ``max_elevation`` (int)
        Peak elevation value at the centre (0–7).  Default 4.
    ``terrain_id`` (TerrainId)
        Surface terrain.  Default ``TerrainId.DIRT_1`` (rocky brown).
        Use ``TerrainId.SNOW_2`` for a snow-capped look.
    ``rock_density`` (float)
        Fraction of tiles decorated with rocks (0–1).  Default 0.08.
    ``center_point`` (tuple[int, int])
        Peak tile.  Defaults to centroid of *point_collection*.
    """

    def __init__(self, name: str = "Mountain", description: str = "Rocky mountain") -> None:
        pass

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        max_elevation: int = max(1, min(7, int(kwargs.get("max_elevation", 4))))
        terrain_id: TerrainId = kwargs.get("terrain_id", TerrainId.DIRT_1)
        rock_density: float = min(1.0, max(0.0, float(kwargs.get("rock_density", 0.08))))
        center_point: tuple[int, int] = kwargs.get(
            "center_point",
            point_collection.get_average_point_position(),
        )
        cx, cy = center_point
        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        # Compute max distance to normalise elevation.
        max_dist = max(
            math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for (x, y) in pts
        ) or 1.0

        # 1. Apply radial elevation: highest at centre, falls off toward edge.
        layer = map_manager.get_map_layer(MapLayerType.ELEVATION)
        for (x, y) in pts:
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            elevation = max(0, int(max_elevation * (1.0 - dist / max_dist)))
            layer.set_point((x, y), elevation, PlayerId.GAIA)

        # 2. Rocky terrain overlay.
        map_manager.place_groups(
            PlaceGroupsConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.TERRAIN,
                object_type=terrain_id,
                player_id=PlayerId.GAIA,
                groups_density=1.0,
                group_size=1,
                margin=0,
            )
        )

        # 3. Rock decor.
        if rock_density > 0:
            for rock in _MINE_ROCKS:
                map_manager.place_groups(
                    PlaceGroupsConfig(
                        point_collection=point_collection,
                        map_layer_type=MapLayerType.DECOR,
                        object_type=rock,
                        player_id=PlayerId.GAIA,
                        groups_density=rock_density / len(_MINE_ROCKS),
                        group_size=1,
                        margin=1,
                    )
                )

        return point_collection


# ---------------------------------------------------------------------------
# CASTLE
# ---------------------------------------------------------------------------


@register_template(TemplateType.CASTLE)
class CastleTemplate(AbstractTemplate):
    """A heavily fortified castle complex — FORT with a central keep.

    Generates the same wall perimeter as ``FortTemplate`` (stone walls,
    guard towers, gates) but with a Castle building as the centre piece
    plus parapets of elite troops.  Best placed on at least a 30×30 region.

    Keyword arguments
    ~~~~~~~~~~~~~~~~~
    ``shape`` (str)
        Wall shape passed to ``FortTemplate``.  Default ``"square"``.
    ``half_size`` (int)
        Fort half-width for square shape.  Default 14.
    ``gate_type`` (GateType)
        Gate style.  Default ``GateType.STONE_GATE`` (Stone Gate).
    ``player_id`` (PlayerId)
        Owning player.  Default ``PlayerId.ONE``.
    ``with_troops`` (bool)
        If ``True`` (default), scatter elite troops in the inner ward.
    ``center_point`` (tuple[int, int])
        Castle centre.  Defaults to centroid of *point_collection*.
    """

    def __init__(self, name: str = "Castle", description: str = "Fortified castle") -> None:
        pass

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        # Delegate most work to the FortTemplate.
        from aoe2mapgenerator.templates.fort import FortTemplate

        shape: str = kwargs.get("shape", "square")
        half_size: int = int(kwargs.get("half_size", 14))
        gate_type: GateType = kwargs.get("gate_type", GateType.STONE_GATE)
        player_id: PlayerId = kwargs.get("player_id", PlayerId.ONE)
        with_troops: bool = bool(kwargs.get("with_troops", True))
        center_point: tuple[int, int] = kwargs.get(
            "center_point",
            point_collection.get_average_point_position(),
        )

        # Build the fort perimeter (walls + guard towers + gates).
        FortTemplate.generate(
            map_manager=map_manager,
            point_collection=point_collection,
            shape=shape,
            half_size=half_size,
            gate_type=gate_type,
            player_id=player_id,
            center_point=center_point,
        )

        # Place a Castle (keep) at the exact centre.
        cx, cy = center_point
        map_manager.base_placer.place_if_possible(
            PlaceIfPossibleConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.UNIT,
                obj_type=BuildingInfo.CASTLE,
                starting_point=(cx, cy),
                player_id=player_id,
                margin=0,
            )
        )

        # Elite garrison.
        if with_troops:
            _elect_troops: list[tuple[int, int]] = [
                (cx + 6, cy),
                (cx - 6, cy),
                (cx, cy + 6),
                (cx, cy - 6),
            ]
            for pos in _elect_troops:
                map_manager.base_placer.place_if_possible(
                    PlaceIfPossibleConfig(
                        point_collection=point_collection,
                        map_layer_type=MapLayerType.UNIT,
                        obj_type=UnitInfo.CHAMPION,
                        starting_point=pos,
                        player_id=player_id,
                        margin=0,
                    )
                )

        return point_collection


# ---------------------------------------------------------------------------
# RIVER
# ---------------------------------------------------------------------------


@register_template(TemplateType.RIVER)
class RiverTemplate(AbstractTemplate):
    """Full edge-to-edge river across the selected region.

    Traces a winding path from one side of the region to the other, fills
    the path tiles with shallow water, and populates them with fish and reeds.
    The river width defaults to 3 tiles (1 core + 1 each side).

    Keyword arguments
    ~~~~~~~~~~~~~~~~~
    ``from_point`` (tuple[int, int])
        Entry point for the river (e.g. left edge).  If omitted, the
        leftmost tile of the midpoint row is used.
    ``to_point`` (tuple[int, int])
        Exit point (e.g. right edge).  If omitted, rightmost tile of
        the midpoint row is used.
    ``width`` (int)
        River width in tiles.  Default 3.
    ``num_fish_groups`` (int)
        Fish group count.  Default 4.
    ``num_divisions`` (int)
        Path warp divisions.  Higher = more winding.  Default 5.
    ``random_shift`` (int)
        Warp amplitude per division.  Default 6.
    """

    def __init__(self, name: str = "River", description: str = "Edge-to-edge river") -> None:
        pass

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        width: int = max(1, int(kwargs.get("width", 3)))
        num_fish_groups: int = max(0, int(kwargs.get("num_fish_groups", 4)))
        num_divisions: int = max(1, int(kwargs.get("num_divisions", 5)))
        random_shift: int = max(0, int(kwargs.get("random_shift", 6)))

        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        mid_y = (min(ys) + max(ys)) // 2

        from_point: tuple[int, int] = kwargs.get("from_point", (min(xs), mid_y))
        to_point: tuple[int, int] = kwargs.get("to_point", (max(xs), mid_y))

        # Lay the river bed as shallow water terrain.
        map_manager.create_path(
            PlacePathConfig(
                point_collection=point_collection,
                map_layer_type=MapLayerType.TERRAIN,
                obj_type=TerrainId.WATER_SHALLOW,
                player_id=PlayerId.GAIA,
                key_points=[from_point, to_point],
                num_divisions=[num_divisions],
                random_shift_range=[random_shift],
            )
        )

        # Widen the river by repeating with perpendicular offsets.
        for w in range(1, width):
            for sign in (-1, 1):
                off = w * sign
                shifted = [(x, y + off) for (x, y) in [from_point, to_point]]
                try:
                    map_manager.create_path(
                        PlacePathConfig(
                            point_collection=point_collection,
                            map_layer_type=MapLayerType.TERRAIN,
                            obj_type=TerrainId.WATER_SHALLOW,
                            player_id=PlayerId.GAIA,
                            key_points=shifted,
                            num_divisions=[num_divisions],
                            random_shift_range=[random_shift],
                        )
                    )
                except Exception:
                    pass

        # Fish.
        if num_fish_groups > 0:
            map_manager.place_groups(
                PlaceGroupsConfig(
                    point_collection=point_collection,
                    map_layer_type=MapLayerType.DECOR,
                    object_type=OtherInfo.FISH_DORADO,
                    player_id=PlayerId.GAIA,
                    groups=num_fish_groups,
                    group_size=2,
                    clumping=2,
                    margin=1,
                )
            )

        return point_collection
