"""Validation helpers for deterministic CITY layout generation."""

from __future__ import annotations

from dataclasses import dataclass, field

from aoe2mapgenerator.templates.city_layout_plan import CityLayoutPlan, PlacedGate

Point = tuple[int, int]


@dataclass
class CityLayoutValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class CityLayoutValidator:
    """Performs structural checks on gates, roads, and wards."""

    @staticmethod
    def validate_gate_count(gates: list[PlacedGate], expected: int = 8) -> CityLayoutValidationResult:
        result = CityLayoutValidationResult(ok=True)
        if len(gates) != expected:
            result.add_error(f"Expected {expected} gates, found {len(gates)}")
        sectors = [g.sector for g in gates]
        if len(set(sectors)) != len(sectors):
            result.add_error(f"Duplicate gate sectors detected: {sectors}")
        return result

    @staticmethod
    def validate_gate_road_reach(gates: list[PlacedGate], road_points: set[Point]) -> CityLayoutValidationResult:
        result = CityLayoutValidationResult(ok=True)
        if not gates:
            result.add_error("No gates found for gate-road validation")
            return result
        for gate in gates:
            gr, gc = gate.inner_approach_tile
            has_adjacent_road = any(
                (gr + dr, gc + dc) in road_points
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
            )
            if not has_adjacent_road and (gr, gc) not in road_points:
                result.add_error(f"Gate {gate.sector} at {gate.gate_center_tile} has no road near inner approach {gate.inner_approach_tile}")
        return result

    @staticmethod
    def validate_wards(plan: CityLayoutPlan, minimum_tiles: int = 25) -> CityLayoutValidationResult:
        result = CityLayoutValidationResult(ok=True)
        for sector, coll in plan.ward_masks.items():
            count = len(coll.get_point_list())
            if count < minimum_tiles:
                result.add_error(f"Ward {sector} too small: {count} tiles")
        for aggregate in ("military", "market", "village"):
            if aggregate not in plan.aggregate_trigger_areas:
                result.add_error(f"Missing aggregate trigger area for {aggregate}")
        return result

