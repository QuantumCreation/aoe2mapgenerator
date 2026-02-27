"""
pytest-benchmark configuration for the performance test suite.

Running benchmarks
------------------
    # Run all benchmarks and save baseline:
    poetry run pytest src/aoe2mapgenerator/unit_tests/performance/ \\
        --benchmark-save=baseline \\
        --benchmark-columns=min,mean,stddev,rounds

    # Compare against saved baseline — FAIL if mean is >50% slower (CI gate):
    poetry run pytest src/aoe2mapgenerator/unit_tests/performance/ \\
        --benchmark-compare=baseline \\
        --benchmark-compare-fail=mean:50%

    # Advisory-only (no failure on regression):
    poetry run pytest src/aoe2mapgenerator/unit_tests/performance/ \\
        --benchmark-compare=baseline

CI usage
--------
The recommended CI command uses ``--benchmark-compare-fail=mean:50%`` so that
a ≥50% mean-time regression for any benchmark causes the job to exit non-zero.
Regressions below 50% are displayed in the comparison table but do not fail CI.

Skipping benchmarks during normal test runs
-------------------------------------------
Benchmarks are marked with ``@pytest.mark.benchmark`` (auto-applied to any
function whose name starts with ``bench_*`` by pytest-benchmark).  To skip
them during the normal test suite:

    poetry run pytest --benchmark-skip src/aoe2mapgenerator/unit_tests/

"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "perf: performance / benchmark test (slow); skip with -m 'not perf'",
    )
