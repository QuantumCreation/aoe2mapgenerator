#!/usr/bin/env python
"""Tier 1 — fast visual rendering.

Builds a named recipe and renders a composite PNG (terrain base + decor +
units) using a single ``imshow`` call per map — ~100× faster than the legacy
per-tile ``hlines`` renderer.

Single map:
    python tools/render_map.py --recipe city --seed 3

Contact sheet (N seeds of the same recipe in one grid — the key artifact for
judging *variety*):
    python tools/render_map.py --recipe forest --seeds 1,2,3,4,5,6,7,8

Output goes to ``tools/out/`` by default.
"""

from __future__ import annotations

import argparse
import os
import sys

from aoe2mapgenerator.evaluation.render import (
    render_composite,
    save_composite,
    save_contact_sheet,
)
from aoe2mapgenerator.recipes import RECIPE_NAMES, build_recipe

DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "out")


def _parse_seeds(spec: str) -> list[int]:
    """Parse '1,2,3' or '1..8' into a list of ints."""
    spec = spec.strip()
    if ".." in spec:
        lo, hi = spec.split("..", 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(",") if s.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fast map rendering")
    parser.add_argument("--recipe", required=True, choices=RECIPE_NAMES)
    parser.add_argument("--seed", type=int, default=0, help="Single seed to render")
    parser.add_argument(
        "--seeds",
        default=None,
        help="Contact sheet: comma list ('1,2,3') or range ('1..8')",
    )
    parser.add_argument("--map-size", type=int, default=None)
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output directory")
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)

    if args.seeds:
        seeds = _parse_seeds(args.seeds)
        images, labels = [], []
        for s in seeds:
            mg = build_recipe(args.recipe, seed=s, map_size=args.map_size)
            images.append(render_composite(mg))
            labels.append(f"seed {s}")
        path = os.path.join(args.out, f"{args.recipe}_seeds_{seeds[0]}-{seeds[-1]}.png")
        save_contact_sheet(
            images, path, labels=labels, title=f"{args.recipe} — {len(seeds)} seeds"
        )
        print(f"Contact sheet: {path}")
        return 0

    mg = build_recipe(args.recipe, seed=args.seed, map_size=args.map_size)
    path = os.path.join(args.out, f"{args.recipe}_{args.seed}.png")
    save_composite(mg, path, title=f"{args.recipe} seed={args.seed}")
    print(f"Saved: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
