"""
Benchmarks for ObjectInfo — measures Enum-by-name lookup cost.

Before the lru_cache fix (Finding 4), each call reconstructs an ObjectSize
Enum member from a name string.  After the fix, cost is amortised O(1).
"""

from __future__ import annotations

import pytest
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.units.placers.object_info import ObjectInfo


_SAMPLE_TYPES = [
    UnitInfo.MILITIA,
    UnitInfo.ARCHER,
    UnitInfo.KNIGHT,
    UnitInfo.MANGUDAI,
    UnitInfo.TREBUCHET_PACKED,
]


@pytest.mark.benchmark(group="object_info_single")
@pytest.mark.parametrize("obj_type", _SAMPLE_TYPES)
def test_bench_object_info_get_size(benchmark, obj_type) -> None:
    """Single get_object_size call — should become O(1) after lru_cache."""
    benchmark(ObjectInfo.get_object_size, obj_type)


@pytest.mark.benchmark(group="object_info_burst")
def test_bench_object_info_burst(benchmark) -> None:
    """50 000 successive get_object_size lookups — mirrors place_groups workload."""
    def run() -> None:
        for _ in range(50_000):
            ObjectInfo.get_object_size(UnitInfo.MILITIA)

    benchmark(run)


@pytest.mark.benchmark(group="object_info_burst")
def test_bench_object_info_effective_size_burst(benchmark) -> None:
    """50 000 get_object_effective_size calls with margin — mirrors _place_single."""
    def run() -> None:
        for _ in range(50_000):
            ObjectInfo.get_object_effective_size(UnitInfo.MILITIA, 1)

    benchmark(run)
