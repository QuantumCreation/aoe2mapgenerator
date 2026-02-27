"""Geometry and deterministic painting helpers for the CITY template."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import GateObject, GateType, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection
from aoe2mapgenerator.units.utils import connect_points
from aoe2mapgenerator.templates.city_layout_plan import GateAnchorSpec, PlacedGate

Point = tuple[int, int]

SECTOR_ORDER: tuple[str, ...] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
SECTOR_VECTORS_FLOAT: dict[str, tuple[float, float]] = {
    "N": (-1.0, 0.0),
    "NE": (-1 / math.sqrt(2), 1 / math.sqrt(2)),
    "E": (0.0, 1.0),
    "SE": (1 / math.sqrt(2), 1 / math.sqrt(2)),
    "S": (1.0, 0.0),
    "SW": (1 / math.sqrt(2), -1 / math.sqrt(2)),
    "W": (0.0, -1.0),
    "NW": (-1 / math.sqrt(2), -1 / math.sqrt(2)),
}
SECTOR_VECTORS_INT: dict[str, Point] = {
    "N": (-1, 0),
    "NE": (-1, 1),
    "E": (0, 1),
    "SE": (1, 1),
    "S": (1, 0),
    "SW": (1, -1),
    "W": (0, -1),
    "NW": (-1, -1),
}


def clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def sign(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def distance_sq(a: Point, b: Point) -> int:
    dr = a[0] - b[0]
    dc = a[1] - b[1]
    return dr * dr + dc * dc


def manhattan(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def to_point_collection(points: Iterable[Point]) -> PointCollection:
    coll = PointCollection()
    coll.add_points(set(points))
    return coll


def filter_points_in_circle(points: Iterable[Point], center: Point, radius: float) -> set[Point]:
    radius_sq = radius * radius
    cr, cc = center
    out: set[Point] = set()
    for r, c in points:
        dr = r - cr
        dc = c - cc
        if dr * dr + dc * dc <= radius_sq:
            out.add((r, c))
    return out


def filter_points_in_annulus(
    points: Iterable[Point],
    center: Point,
    inner_radius: float,
    outer_radius: float,
) -> set[Point]:
    inner_sq = inner_radius * inner_radius
    outer_sq = outer_radius * outer_radius
    cr, cc = center
    out: set[Point] = set()
    for r, c in points:
        dr = r - cr
        dc = c - cc
        d2 = dr * dr + dc * dc
        if inner_sq <= d2 <= outer_sq:
            out.add((r, c))
    return out


def sector_for_point(center: Point, point: Point) -> str:
    """Map a point to the nearest compass sector in row/col coordinates."""
    dr = point[0] - center[0]
    dc = point[1] - center[1]
    if dr == 0 and dc == 0:
        return "N"
    best_sector = "N"
    best_score = -10**9
    best_axis_penalty = 10**9
    for sector in SECTOR_ORDER:
        vr, vc = SECTOR_VECTORS_FLOAT[sector]
        score = dr * vr + dc * vc
        # Tie-break toward cleaner alignment within a sector.
        axis_penalty = abs(dr * vc - dc * vr)
        if score > best_score or (math.isclose(score, best_score) and axis_penalty < best_axis_penalty):
            best_sector = sector
            best_score = score
            best_axis_penalty = axis_penalty
    return best_sector


def points_by_sector(points: Iterable[Point], center: Point) -> dict[str, set[Point]]:
    out = {s: set() for s in SECTOR_ORDER}
    for point in points:
        out[sector_for_point(center, point)].add(point)
    return out


def _face_center_tiebreak(center: Point, sector: str, point: Point) -> tuple[float, float]:
    """Score tuple for selecting a gate anchor on a wall face."""
    dr = point[0] - center[0]
    dc = point[1] - center[1]
    vr, vc = SECTOR_VECTORS_FLOAT[sector]
    primary = dr * vr + dc * vc
    # Lower orthogonal deviation is better.
    orth = abs(dr * vc - dc * vr)
    return (primary, -orth)


def compute_gate_anchor_specs(wall_points: list[Point], center: Point) -> list[GateAnchorSpec]:
    """Compute deterministic 8-sector gate anchors from wall points (row/col aware)."""
    if not wall_points:
        return []
    specs: list[GateAnchorSpec] = []
    used: set[Point] = set()
    for idx, sector in enumerate(SECTOR_ORDER):
        candidates = [p for p in wall_points if p not in used]
        if not candidates:
            candidates = wall_points
        target = max(
            candidates,
            key=lambda p: (_face_center_tiebreak(center, sector, p), -distance_sq(center, p)),
        )
        used.add(target)
        is_diag = sector in {"NE", "SE", "SW", "NW"}
        inward = tuple(-v for v in SECTOR_VECTORS_INT[sector])  # type: ignore[misc]
        outward = SECTOR_VECTORS_INT[sector]
        specs.append(
            GateAnchorSpec(
                sector=sector,
                target_wall_anchor=target,
                priority=idx,
                expected_orientation="diagonal" if is_diag else "cardinal",
                inward_vector=inward,  # row/col
                outward_vector=outward,
            )
        )
    return specs


def _gate_buildings_for_type(gate_type: GateType) -> list[BuildingInfo]:
    buildings: list[BuildingInfo] = []
    for gate_object in GateType.get_gate_objects_from_gate_type(gate_type):
        buildings.append(BuildingInfo[gate_object.value])
    return buildings


def _footprint_from_gate_center(gate_center: Point, gate_object_name: str) -> list[Point]:
    gate_object = GateObject[gate_object_name]
    dims = list(gate_object.get_gate_dimensions())
    real_offset = dims[2]
    anchor = (gate_center[0] - real_offset[0], gate_center[1] - real_offset[1])
    return [(anchor[0] + dr, anchor[1] + dc) for dr, dc in dims]


def _approach_point(gate_center: Point, footprint: set[Point], direction: Point, map_size: int) -> Point:
    r, c = gate_center
    dr, dc = direction
    for _ in range(5):
        nr = clamp_int(r + dr, 0, map_size - 1)
        nc = clamp_int(c + dc, 0, map_size - 1)
        r, c = nr, nc
        if (r, c) not in footprint:
            return (r, c)
    return (r, c)


def capture_placed_gates(
    map_manager: IMapManager,
    gate_type: GateType,
    center: Point,
    player_id: PlayerId,
) -> list[PlacedGate]:
    """Scan the UNIT layer and return actual placed gates with sector classification."""
    raw: list[PlacedGate] = []
    map_size = map_manager.get_map().size
    for building in _gate_buildings_for_type(gate_type):
        gate_centers = map_manager.get_set_with_map_object(
            map_layer_type=MapLayerType.UNIT,
            obj=MapObject(building, player_id),
        )
        for gate_center in gate_centers:
            footprint = _footprint_from_gate_center(gate_center, building._name_)
            footprint_set = set(footprint)
            sector = sector_for_point(center, gate_center)
            inward_vec = tuple(-v for v in SECTOR_VECTORS_INT[sector])  # type: ignore[misc]
            outward_vec = SECTOR_VECTORS_INT[sector]
            inner = _approach_point(gate_center, footprint_set, inward_vec, map_size)
            outer = _approach_point(gate_center, footprint_set, outward_vec, map_size)
            raw.append(
                PlacedGate(
                    sector=sector,
                    gate_center_tile=gate_center,
                    gate_object_name=building._name_,
                    footprint_tiles=footprint,
                    inner_approach_tile=inner,
                    outer_approach_tile=outer,
                )
            )

    # De-duplicate by gate center and enforce deterministic sector uniqueness (prefer nearest sector anchor).
    dedup = {(g.gate_center_tile, g.gate_object_name): g for g in raw}
    gates = list(dedup.values())
    gates.sort(key=lambda g: (SECTOR_ORDER.index(g.sector), g.gate_center_tile))

    per_sector: dict[str, PlacedGate] = {}
    for gate in gates:
        existing = per_sector.get(gate.sector)
        if existing is None or distance_sq(gate.gate_center_tile, center) > distance_sq(existing.gate_center_tile, center):
            per_sector[gate.sector] = gate
    ordered = [per_sector[s] for s in SECTOR_ORDER if s in per_sector]
    return ordered


def nearest_point(reference: Point, candidates: Iterable[Point]) -> Point:
    candidates_list = list(candidates)
    if not candidates_list:
        return reference
    return min(candidates_list, key=lambda p: distance_sq(reference, p))


def _width_offsets(width: int) -> list[Point]:
    if width <= 1:
        return [(0, 0)]
    if width == 2:
        return [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
    # width >= 3: square brush radius 1 (good-looking, deterministic)
    return [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]


@dataclass
class RoadCorridorPainter:
    """Deterministically paints road corridors by rasterizing exact polylines."""

    map_manager: IMapManager
    allowed_points: set[Point]
    player_id: PlayerId
    painted: dict[str, set[Point]]

    def __init__(self, map_manager: IMapManager, allowed_points: set[Point], player_id: PlayerId):
        self.map_manager = map_manager
        self.allowed_points = allowed_points
        self.player_id = player_id
        self.painted = {}

    def paint_polyline(self, key_points: list[Point], terrain_obj, width: int, key: str) -> set[Point]:
        if len(key_points) < 2:
            return set()
        path = [tuple(p) for p in connect_points(key_points)]
        painted: set[Point] = set()
        brush = _width_offsets(width)
        aoe_map = self.map_manager.get_map()
        for r, c in path:
            for dr, dc in brush:
                p = (r + dr, c + dc)
                if p not in self.allowed_points:
                    continue
                aoe_map.set_point(p, terrain_obj, MapLayerType.TERRAIN, self.player_id)
                painted.add(p)
        self.painted[key] = painted
        return painted

    def paint_circle_patch(self, center: Point, radius: int, terrain_obj, key: str) -> set[Point]:
        cr, cc = center
        painted: set[Point] = set()
        aoe_map = self.map_manager.get_map()
        r_sq = radius * radius
        for r in range(cr - radius, cr + radius + 1):
            for c in range(cc - radius, cc + radius + 1):
                if (r, c) not in self.allowed_points:
                    continue
                dr = r - cr
                dc = c - cc
                if dr * dr + dc * dc > r_sq:
                    continue
                aoe_map.set_point((r, c), terrain_obj, MapLayerType.TERRAIN, self.player_id)
                painted.add((r, c))
        self.painted[key] = painted
        return painted

