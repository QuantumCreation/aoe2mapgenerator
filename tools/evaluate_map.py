#!/usr/bin/env python
"""Tier 0 — headless map-quality evaluation.

Builds a named recipe and prints a PASS/WARN/FAIL quality report computed from
the raw map matrices. No display, no matplotlib — runs in well under a second
and is CI-able.

Usage:
    python tools/evaluate_map.py --recipe city --seed 3
    python tools/evaluate_map.py --recipe forest --seed 1 --scatter decor
    python tools/evaluate_map.py --all --seed 42

Exit code is 0 when every metric passes (WARN tolerated), 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import sys

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.evaluation.metrics import compute_report
from aoe2mapgenerator.recipes import RECIPE_NAMES, RECIPES, build_recipe


def _parse_layer(name: str | None) -> MapLayerType | None:
    if not name:
        return None
    try:
        return MapLayerType[name.upper()]
    except KeyError as e:
        raise SystemExit(f"Unknown layer {name!r}. Use one of: {[m.name for m in MapLayerType]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Headless map-quality evaluation")
    parser.add_argument("--recipe", choices=RECIPE_NAMES, help="Recipe to build")
    parser.add_argument("--all", action="store_true", help="Evaluate every recipe")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed")
    parser.add_argument(
        "--scatter",
        default=None,
        help="Layer to run the evenness metric on (e.g. decor). Overrides recipe default.",
    )
    parser.add_argument("--map-size", type=int, default=None, help="Override map size")
    args = parser.parse_args(argv)

    if not args.all and not args.recipe:
        parser.error("provide --recipe <name> or --all")

    names = RECIPE_NAMES if args.all else [args.recipe]
    any_fail = False

    for name in names:
        mg = build_recipe(name, seed=args.seed, map_size=args.map_size)
        scatter = _parse_layer(args.scatter)
        if scatter is None:
            scatter = RECIPES[name].scatter_layer
        report = compute_report(mg, scatter_layer=scatter)
        print(f"\n=== recipe: {name}  (seed={args.seed}) ===")
        print(report.to_text())
        if not report.all_pass():
            any_fail = True

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
