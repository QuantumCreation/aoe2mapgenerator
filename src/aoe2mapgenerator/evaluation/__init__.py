"""Headless map-quality evaluation (Tier 0 of the iteration loop)."""

from aoe2mapgenerator.evaluation.metrics import (
    FAIL,
    PASS,
    WARN,
    MapReport,
    MetricResult,
    bounds,
    compute_report,
    coverage,
    nearest_neighbor_stats,
)
from aoe2mapgenerator.evaluation.render import (
    render_composite,
    save_composite,
    save_contact_sheet,
)

__all__ = [
    "PASS",
    "WARN",
    "FAIL",
    "MetricResult",
    "MapReport",
    "coverage",
    "nearest_neighbor_stats",
    "bounds",
    "compute_report",
    "render_composite",
    "save_composite",
    "save_contact_sheet",
]
