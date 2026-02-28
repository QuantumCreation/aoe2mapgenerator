"""High-level trigger orchestration for city-life behavior.

This module builds layered movement logic so generated cities feel active:
- district street patrols
- gate rotation patrols
- long-range expedition patrols
- villager work routes (farm/mine/forage)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, TYPE_CHECKING

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.triggers.triggers import TriggerManager

if TYPE_CHECKING:
    from aoe2mapgenerator.templates.city_district_templates import DistrictPlacementResult

Point = tuple[int, int]


@dataclass(frozen=True)
class TriggerArea:
    """Rectangular area used by trigger effects."""

    x1: int
    y1: int
    x2: int
    y2: int

    def clamped(self, map_size: int) -> "TriggerArea":
        return TriggerArea(
            x1=max(0, min(map_size - 1, self.x1)),
            y1=max(0, min(map_size - 1, self.y1)),
            x2=max(0, min(map_size - 1, self.x2)),
            y2=max(0, min(map_size - 1, self.y2)),
        )

    def center(self) -> Point:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @staticmethod
    def from_center(point: Point, padding: int) -> "TriggerArea":
        x, y = point
        return TriggerArea(x - padding, y - padding, x + padding, y + padding)


def _nearest_point(reference: Point, candidates: Sequence[Point]) -> Point:
    if not candidates:
        return reference
    return min(candidates, key=lambda p: (p[0] - reference[0]) ** 2 + (p[1] - reference[1]) ** 2)


def _split_area(area: TriggerArea, parts: int = 3) -> list[TriggerArea]:
    if parts <= 1:
        return [area]
    width = max(1, area.x2 - area.x1 + 1)
    step = max(1, width // parts)
    out: list[TriggerArea] = []
    start = area.x1
    for idx in range(parts):
        end = area.x2 if idx == parts - 1 else min(area.x2, start + step - 1)
        out.append(TriggerArea(start, area.y1, end, area.y2))
        start = end + 1
        if start > area.x2:
            break
    return out


def _district_area(result: "DistrictPlacementResult") -> TriggerArea | None:
    if result.patrol_area is None:
        return None
    x1, y1, x2, y2 = result.patrol_area
    return TriggerArea(x1, y1, x2, y2)


def apply_city_life_triggers(
    map_manager: IMapManager,
    district_results: Sequence["DistrictPlacementResult"],
    gate_points: Sequence[Point],
    city_center: Point,
    player_id: PlayerId,
    villager_targets: Dict[str, Point],
    palace_center: Point | None = None,
    edge_margin: int = 6,
) -> int:
    """Create a robust city-life trigger set and return trigger count created."""
    # Lazily initialize the scenario if it hasn't been created yet.
    # This happens when MapManager is constructed in environments that do not
    # have a custom output_dir pointing at the AoE2 installation (e.g. tests).
    if map_manager.scenario is None:
        from aoe2mapgenerator.scenario.scenario import Scenario  # local to avoid circular
        map_manager.scenario = Scenario(map_manager.map)
    trigger_manager = TriggerManager(map_manager.scenario.get_base_scenario())
    map_size = map_manager.map.size
    created = 0

    district_areas: dict[str, TriggerArea] = {}
    for district in district_results:
        area = _district_area(district)
        if area is None:
            continue
        district_areas[district.name] = area.clamped(map_size)

    # 1) District patrols up/down streets toward nearest gates.
    for district in district_results:
        area = district_areas.get(district.name)
        if area is None:
            continue
        waypoint = _nearest_point(district.center, gate_points)
        trigger_manager.patrol(
            x1=area.x1,
            y1=area.y1,
            x2=area.x2,
            y2=area.y2,
            player_id=player_id,
            x_target=waypoint[0],
            y_target=waypoint[1],
            looping=True,
            trigger_name=f"City Life - {district.name.title()} Street Patrol",
        )
        created += 1

    # 2) Gate-to-gate wall patrols.
    for idx, gate in enumerate(gate_points):
        next_gate = gate_points[(idx + 1) % len(gate_points)]
        area = TriggerArea.from_center(gate, padding=5).clamped(map_size)
        trigger_manager.patrol(
            x1=area.x1,
            y1=area.y1,
            x2=area.x2,
            y2=area.y2,
            player_id=player_id,
            x_target=next_gate[0],
            y_target=next_gate[1],
            looping=True,
            trigger_name=f"City Life - Gate Rotation {idx + 1}",
        )
        created += 1

    # 3) Palace / command-center to gates.
    command_center = palace_center or city_center
    command_area = TriggerArea.from_center(command_center, padding=8).clamped(map_size)
    for idx, gate in enumerate(gate_points):
        trigger_manager.patrol(
            x1=command_area.x1,
            y1=command_area.y1,
            x2=command_area.x2,
            y2=command_area.y2,
            player_id=player_id,
            x_target=gate[0],
            y_target=gate[1],
            looping=True,
            trigger_name=f"City Life - Command Route {idx + 1}",
        )
        created += 1

    # 4) Expedition patrols from military district and palace to world edges.
    military_area = district_areas.get("military", command_area)
    edge_targets = [
        (city_center[0], edge_margin),
        (map_size - 1 - edge_margin, city_center[1]),
        (city_center[0], map_size - 1 - edge_margin),
        (edge_margin, city_center[1]),
    ]
    for idx, edge in enumerate(edge_targets):
        source_area = military_area if idx % 2 == 0 else command_area
        trigger_manager.patrol(
            x1=source_area.x1,
            y1=source_area.y1,
            x2=source_area.x2,
            y2=source_area.y2,
            player_id=player_id,
            x_target=edge[0],
            y_target=edge[1],
            looping=True,
            trigger_name=f"City Life - Expedition {idx + 1}",
        )
        created += 1

    # 5) Villager economic work: assign tasks + movement routes.
    village_area = district_areas.get("village")
    if village_area is not None and villager_targets:
        worker_areas = _split_area(village_area, parts=max(1, len(villager_targets)))
        for idx, (label, target) in enumerate(villager_targets.items()):
            worker_area = worker_areas[idx % len(worker_areas)].clamped(map_size)
            trigger_manager.task_units_to_point(
                x1=worker_area.x1,
                y1=worker_area.y1,
                x2=worker_area.x2,
                y2=worker_area.y2,
                target_x=target[0],
                target_y=target[1],
                player_id=player_id,
                looping=True,
                trigger_name=f"City Life - Villager Task {label}",
            )
            created += 1

            trigger_manager.patrol(
                x1=worker_area.x1,
                y1=worker_area.y1,
                x2=worker_area.x2,
                y2=worker_area.y2,
                player_id=player_id,
                x_target=target[0],
                y_target=target[1],
                looping=True,
                trigger_name=f"City Life - Villager Route {label}",
            )
            created += 1

    return created
