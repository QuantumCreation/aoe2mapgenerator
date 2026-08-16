"""Headless map-quality metrics (Tier 0 of the iteration loop).

These are **pure** functions over plain data (point lists and object matrices)
with no I/O and no matplotlib. They run in well under a second and are the
automated gate: a generation change is not reviewed visually until its metrics
pass.

The public entry point is :func:`compute_report`, which takes a ``MapManager``
and returns a :class:`MapReport` of PASS/WARN/FAIL results. The individual
metric functions are exposed so tests and the CLI can call them directly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from aoe2mapgenerator.map.map_manager import MapManager

# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


@dataclass(frozen=True)
class MetricResult:
    """A single metric outcome."""

    name: str
    status: str  # PASS | WARN | FAIL
    value: float
    detail: str


@dataclass
class MapReport:
    """The full set of metric results for one generated map."""

    results: list[MetricResult] = field(default_factory=list)

    def add(self, result: MetricResult) -> None:
        self.results.append(result)

    def all_pass(self) -> bool:
        """True when no metric is a hard FAIL (WARN is tolerated)."""
        return all(r.status != FAIL for r in self.results)

    def failures(self) -> list[MetricResult]:
        return [r for r in self.results if r.status == FAIL]

    def to_text(self) -> str:
        lines = []
        for r in self.results:
            lines.append(f"  [{r.status:<4}] {r.name:<22} {r.value:>10.3f}  {r.detail}")
        header = "MAP QUALITY REPORT"
        footer = "RESULT: " + ("PASS" if self.all_pass() else "FAIL")
        return "\n".join([header, *lines, footer])


# ---------------------------------------------------------------------------
# Pure metric functions
# ---------------------------------------------------------------------------


def coverage(points: Sequence[tuple[int, int]], total_tiles: int) -> float:
    """Fraction of tiles occupied by the given points (0.0–1.0)."""
    if total_tiles <= 0:
        return 0.0
    return len(set(points)) / total_tiles


def nearest_neighbor_stats(
    points: Sequence[tuple[int, int]],
) -> tuple[float, float, float]:
    """Return (mean, std, cv) of nearest-neighbor distances.

    ``cv`` (coefficient of variation = std/mean) is the evenness signal:
    a tight scatter has a low, stable cv; clumps or gaps push it up.
    Returns (0, 0, 0) when there are fewer than two points.
    """
    pts = list(points)
    n = len(pts)
    if n < 2:
        return 0.0, 0.0, 0.0

    dists: list[float] = []
    for i in range(n):
        xi, yi = pts[i]
        best = float("inf")
        for j in range(n):
            if i == j:
                continue
            xj, yj = pts[j]
            d = math.hypot(xi - xj, yi - yj)
            if d < best:
                best = d
        dists.append(best)

    mean = sum(dists) / n
    variance = sum((d - mean) ** 2 for d in dists) / n
    std = math.sqrt(variance)
    cv = (std / mean) if mean > 0 else 0.0
    return mean, std, cv


def bounds(
    points: Sequence[tuple[int, int]], size: int
) -> tuple[tuple[int, int], tuple[int, int], bool]:
    """Return (min_xy, max_xy, in_bounds) for a set of points.

    ``in_bounds`` is True when every point lies within ``[0, size)`` on both
    axes. Returns ((0,0),(0,0),True) for an empty set.
    """
    if not points:
        return (0, 0), (0, 0), True
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_xy = (min(xs), min(ys))
    max_xy = (max(xs), max(ys))
    in_bounds = all(0 <= x < size and 0 <= y < size for x, y in points)
    return min_xy, max_xy, in_bounds


def _status_from_cv(cv: float) -> str:
    """Map a coefficient of variation to a status.

    A healthy even scatter has cv well below 1.0. We WARN above 0.9 and FAIL
    above 1.4 (strong clumping or gapping).
    """
    if cv > 1.4:
        return FAIL
    if cv > 0.9:
        return WARN
    return PASS


# ---------------------------------------------------------------------------
# MapManager-facing report builder
# ---------------------------------------------------------------------------


def _layer_points(mg: "MapManager", layer) -> list[tuple[int, int]]:
    """All non-empty tile coordinates for a layer, as (x, y)."""
    from aoe2mapgenerator.common.constants.default_objects import (
        DEFAULT_EMPTY_OBJECT,
    )

    arr = mg.get_array(layer)
    pts: list[tuple[int, int]] = []
    for x, row in enumerate(arr):
        for y, cell in enumerate(row):
            if cell != DEFAULT_EMPTY_OBJECT:
                pts.append((x, y))
    return pts


def compute_report(
    mg: "MapManager",
    scatter_layer=None,
    scatter_cv_warn: float = 0.9,
    scatter_cv_fail: float = 1.4,
) -> MapReport:
    """Compute a quality report for a built map.

    Args:
        mg: A fully built ``MapManager``.
        scatter_layer: Optional layer to run the evenness metric on (e.g. the
            DECOR layer for a forest). When None, evenness is skipped.
        scatter_cv_warn / scatter_cv_fail: Thresholds for the evenness metric.

    Returns:
        A :class:`MapReport`.
    """
    from aoe2mapgenerator.common.enums.enum import MapLayerType

    report = MapReport()
    size = mg.map.size
    total = size * size

    # --- Coverage per populated layer -------------------------------------
    for layer in (
        MapLayerType.TERRAIN,
        MapLayerType.DECOR,
        MapLayerType.UNIT,
    ):
        pts = _layer_points(mg, layer)
        cov = coverage(pts, total)
        # Terrain should be (near) fully covered; decor/units are sparse by
        # design, so only FAIL terrain when it is empty.
        if layer == MapLayerType.TERRAIN:
            status = PASS if cov > 0.9 else (WARN if cov > 0.5 else FAIL)
        else:
            status = PASS
        report.add(
            MetricResult(
                name=f"coverage.{layer.name.lower()}",
                status=status,
                value=cov,
                detail=f"{len(pts)}/{total} tiles",
            )
        )

    # --- Bounds (decor + units must stay on the map) ----------------------
    for layer in (MapLayerType.DECOR, MapLayerType.UNIT):
        pts = _layer_points(mg, layer)
        if not pts:
            continue
        _, _, in_bounds = bounds(pts, size)
        report.add(
            MetricResult(
                name=f"bounds.{layer.name.lower()}",
                status=PASS if in_bounds else FAIL,
                value=1.0 if in_bounds else 0.0,
                detail="all on-map" if in_bounds else "OFF-MAP OBJECTS",
            )
        )

    # --- Evenness (optional scatter layer) --------------------------------
    if scatter_layer is not None:
        pts = _layer_points(mg, scatter_layer)
        mean, std, cv = nearest_neighbor_stats(pts)
        status = _status_from_cv(cv)
        report.add(
            MetricResult(
                name="evenness.scatter",
                status=status,
                value=cv,
                detail=f"nn mean={mean:.2f} std={std:.2f} (n={len(pts)})",
            )
        )

    return report
