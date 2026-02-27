"""
Determinism tests for generate_voronoi_l1.

ZERO TOLERANCE policy: these tests freeze the exact zone-assignment output of
the Voronoi algorithm.  Any future refactoring of the algorithm MUST produce
bit-identical results for every fixture defined below (same seeds → same zone
grid).  If the algorithm has a known correctness bug the test fixture must be
updated intentionally with a commit explaining why, not silently broken.
"""

from __future__ import annotations

import numpy as np
import pytest

from aoe2mapgenerator.units.wallgenerators.voronoi import generate_voronoi_l1

# ---------------------------------------------------------------------------
# Fixture data — seeded cases
# Each entry: (grid_width, grid_height, seed_points, zone_shift)
# ---------------------------------------------------------------------------
_CASES: list[tuple[int, int, list[tuple[int, int]], int]] = [
    # Tiny 5×5, single seed at origin
    (5, 5, [(0, 0)], 1),
    # Tiny 5×5, two seeds
    (5, 5, [(1, 1), (3, 3)], 1),
    # 10×10, four corner seeds
    (10, 10, [(1, 1), (1, 8), (8, 1), (8, 8)], 1),
    # 10×10, tie-breaking line (seeds equidistant from centre column)
    (10, 10, [(0, 4), (0, 5)], 1),
    # 20×20, scattered seeds
    (
        20, 20,
        [
            (2, 2), (2, 17), (10, 10), (17, 2), (17, 17),
            (5, 10), (10, 5), (10, 15), (15, 10),
        ],
        1,
    ),
    # Non-zero zone_shift must not affect spatial assignment
    (10, 10, [(2, 2), (7, 7)], 5),
]


def _case_id(case: tuple) -> str:
    gw, gh, seeds, zs = case
    return f"{gw}x{gh}_s{len(seeds)}_z{zs}"


class TestVoronoiDeterminism:
    """
    Each test verifies that generate_voronoi_l1 satisfies the zero-tolerance
    contract on zone assignment.
    """

    @pytest.mark.parametrize("case", _CASES, ids=[_case_id(c) for c in _CASES])
    def test_output_is_stable_across_calls(
        self, case: tuple[int, int, list[tuple[int, int]], int]
    ) -> None:
        """Identical inputs → identical outputs (no stochastic variation)."""
        gw, gh, seeds, zs = case
        result_a = generate_voronoi_l1(gw, gh, seeds, zone_shift=zs)
        result_b = generate_voronoi_l1(gw, gh, seeds, zone_shift=zs)
        assert result_a == result_b, "generate_voronoi_l1 is not deterministic"

    @pytest.mark.parametrize("case", _CASES, ids=[_case_id(c) for c in _CASES])
    def test_output_shape(
        self, case: tuple[int, int, list[tuple[int, int]], int]
    ) -> None:
        """Output dimensions must match the requested grid size."""
        gw, gh, seeds, zs = case
        result = generate_voronoi_l1(gw, gh, seeds, zone_shift=zs)
        assert len(result) == gw, f"Expected {gw} rows, got {len(result)}"
        assert all(len(row) == gh for row in result), (
            f"Not all rows have {gh} columns"
        )

    @pytest.mark.parametrize("case", _CASES, ids=[_case_id(c) for c in _CASES])
    def test_each_tile_assigned_to_valid_zone(
        self, case: tuple[int, int, list[tuple[int, int]], int]
    ) -> None:
        """Every tile's zone index must fall in [zone_shift, zone_shift + n_seeds)."""
        gw, gh, seeds, zs = case
        result = generate_voronoi_l1(gw, gh, seeds, zone_shift=zs)
        valid = set(range(zs, zs + len(seeds)))
        flat = {cell for row in result for cell in row}
        assert flat <= valid, f"Unexpected zone indices {flat - valid}"

    @pytest.mark.parametrize("case", _CASES, ids=[_case_id(c) for c in _CASES])
    def test_every_seed_zone_present(
        self, case: tuple[int, int, list[tuple[int, int]], int]
    ) -> None:
        """Every seed must own at least one tile (grid is large enough)."""
        gw, gh, seeds, zs = case
        if gw * gh < len(seeds):
            pytest.skip("Grid too small to guarantee every seed owns a tile")
        result = generate_voronoi_l1(gw, gh, seeds, zone_shift=zs)
        flat = {cell for row in result for cell in row}
        all_zones = set(range(zs, zs + len(seeds)))
        assert flat == all_zones, f"Missing zones: {all_zones - flat}"

    @pytest.mark.parametrize("case", _CASES, ids=[_case_id(c) for c in _CASES])
    def test_l1_nearest_seed_assignment(
        self, case: tuple[int, int, list[tuple[int, int]], int]
    ) -> None:
        """
        ZERO TOLERANCE: each tile must be assigned to the seed with the
        minimum L1 distance.  On a tie, the lowest seed index wins
        (np.argmin semantics — consistent with current implementation).
        """
        gw, gh, seeds, zs = case
        result = generate_voronoi_l1(gw, gh, seeds, zone_shift=zs)
        seeds_arr = np.array(seeds)

        for xi in range(gw):
            for yj in range(gh):
                dists = np.abs(seeds_arr[:, 0] - xi) + np.abs(seeds_arr[:, 1] - yj)
                expected_idx = int(np.argmin(dists)) + zs
                actual_idx = result[xi][yj]
                assert actual_idx == expected_idx, (
                    f"Tile ({xi},{yj}): expected zone {expected_idx}, got {actual_idx}"
                )

    def test_zone_shift_does_not_change_spatial_pattern(self) -> None:
        """Changing zone_shift only offsets values; spatial assignment is identical."""
        seeds = [(2, 2), (7, 7)]
        grid_a = generate_voronoi_l1(10, 10, seeds, zone_shift=1)
        grid_b = generate_voronoi_l1(10, 10, seeds, zone_shift=10)
        for xi in range(10):
            for yj in range(10):
                assert grid_b[xi][yj] - grid_a[xi][yj] == 9, (
                    f"Tile ({xi},{yj}): offset mismatch"
                )

    def test_single_seed_owns_all_tiles(self) -> None:
        """A single seed must own every tile regardless of position."""
        result = generate_voronoi_l1(8, 8, [(3, 5)], zone_shift=2)
        assert all(cell == 2 for row in result for cell in row)

    def test_adjacent_seeds_boundary(self) -> None:
        """Seeds at sy=0 and sy=4 on a 8-row × 1-col grid verify L1 tie-breaking.

        grid_width=8, grid_height=1 → rows=8, cols=1.
        col_idx is always 0; row_idx goes 0..7.
        seed (sx=0,sy=0): dist at tile (i,j=0) = |j-0| + |i-0| = i
        seed (sx=0,sy=4): dist at tile (i,j=0) = |j-0| + |i-4| = |i-4|

        After .transpose().tolist() the result is [[v0, v1, ..., v7]] so
        result[0] contains 8 zone values indexed by row.
        """
        result = generate_voronoi_l1(8, 1, [(0, 0), (0, 4)], zone_shift=1)
        zones = result[0]  # 8 zone values, one per row

        # row 0: dist_to_seed0=0 < dist_to_seed1=4 → seed 0 (zone 1)
        assert zones[0] == 1
        # row 2: dist_to_seed0=2 == dist_to_seed1=2 → TIE → argmin → first seed (zone 1)
        assert zones[2] == 1
        # row 3: dist_to_seed0=3 > dist_to_seed1=1 → seed 1 (zone 2)
        assert zones[3] == 2
        # row 7: dist_to_seed0=7 > dist_to_seed1=3 → seed 1 (zone 2)
        assert zones[7] == 2
