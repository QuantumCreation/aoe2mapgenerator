"""Fast ``imshow``-based map rendering (Tier 1 of the iteration loop).

The existing ``Visualizer.visualize_mat`` draws one ``hline``/``vline`` per
tile, which is O(size²) matplotlib primitives — painfully slow for 120×120 maps.
This module instead builds a single RGB numpy image per map and hands it to
``imshow`` once, which is ~100× faster and produces a clean composite:

- **Terrain** as the base color (semantic palette: water/grass/dirt/snow/...).
- **Decor** (trees, bushes) overlaid in green.
- **Units** (buildings, walls, gates) overlaid in red/orange/gray.

Everything is headless (``Agg`` backend) so it runs in CI and in the tools.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing only
    from aoe2mapgenerator.map.map_manager import MapManager

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    plt = None

from aoe2mapgenerator.common.constants.default_objects import DEFAULT_EMPTY_OBJECT
from aoe2mapgenerator.common.enums.enum import MapLayerType

# ---------------------------------------------------------------------------
# Semantic color palettes (RGB, 0-255)
# ---------------------------------------------------------------------------

_BG = (30, 30, 34)  # empty / unknown


def _terrain_color(obj_type: object) -> tuple[int, int, int]:
    """Map a terrain id to a natural color by keyword in its name."""
    name = str(getattr(obj_type, "name", obj_type)).upper()
    if "WATER" in name or "OCEAN" in name or "SEA" in name:
        return (40, 90, 180)
    if "BEACH" in name or "SAND" in name or "DESERT" in name:
        return (214, 196, 140)
    if "SNOW" in name or "ICE" in name or "FROZEN" in name:
        return (235, 240, 245)
    if "GRASS" in name or "MEADOW" in name or "FOREST" in name:
        return (90, 150, 70)
    if "DIRT" in name or "PATH" in name or "ROAD" in name:
        return (150, 110, 70)
    if "ROCK" in name or "STONE" in name or "MOUNTAIN" in name:
        return (120, 120, 125)
    return (110, 130, 90)


def _decor_color(obj_type: object) -> tuple[int, int, int]:
    name = str(getattr(obj_type, "name", obj_type)).upper()
    if "TREE" in name or "OAK" in name or "PINE" in name or "PALM" in name:
        return (30, 100, 40)
    if "BUSH" in name or "FRUIT" in name or "FORAGE" in name or "BERRY" in name:
        return (120, 190, 90)
    return (60, 140, 60)


def _unit_color(obj_type: object) -> tuple[int, int, int]:
    name = str(getattr(obj_type, "name", obj_type)).upper()
    if "GATE" in name:
        return (240, 150, 30)
    if "WALL" in name or "TOWER" in name:
        return (200, 200, 205)
    if "HOUSE" in name or "CASTLE" in name or "BUILDING" in name or "TOWN" in name:
        return (200, 60, 50)
    return (220, 90, 70)


def _layer_category_matrix(
    mg: "MapManager", layer: MapLayerType, color_fn
) -> np.ndarray:
    """Return an (size, size, 3) uint8 RGB image for one layer.

    Empty tiles are transparent (0,0,0) with a separate alpha handled by the
    caller; here we simply return RGB and a boolean mask of non-empty tiles.
    """
    size = mg.map.size
    rgb = np.zeros((size, size, 3), dtype=np.uint8)
    mask = np.zeros((size, size), dtype=bool)
    arr = mg.get_array(layer)
    for x in range(size):
        row = arr[x]
        for y in range(size):
            cell = row[y]
            if cell != DEFAULT_EMPTY_OBJECT:
                r, g, b = color_fn(cell.obj_type)
                rgb[x, y] = (r, g, b)
                mask[x, y] = True
    return rgb, mask


def render_composite(mg: "MapManager") -> np.ndarray:
    """Render a single composite RGB image (size, size, 3) for a map.

    Terrain is the base; decor and units are overlaid where present.
    """
    size = mg.map.size
    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:] = _BG

    # Terrain base.
    terrain_rgb, terrain_mask = _layer_category_matrix(
        mg, MapLayerType.TERRAIN, _terrain_color
    )
    img[terrain_mask] = terrain_rgb[terrain_mask]

    # Decor overlay (trees/bushes).
    decor_rgb, decor_mask = _layer_category_matrix(
        mg, MapLayerType.DECOR, _decor_color
    )
    img[decor_mask] = decor_rgb[decor_mask]

    # Unit overlay (buildings/walls/gates) on top.
    unit_rgb, unit_mask = _layer_category_matrix(
        mg, MapLayerType.UNIT, _unit_color
    )
    img[unit_mask] = unit_rgb[unit_mask]

    return img


def save_composite(mg: "MapManager", path: str, title: str = "") -> str:
    """Render and save a single composite PNG. Returns the path."""
    if plt is None:
        raise ImportError("matplotlib is required for rendering")
    img = render_composite(mg)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
    ax.imshow(img, interpolation="nearest")
    ax.set_title(title, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def save_contact_sheet(
    images: list[np.ndarray],
    path: str,
    labels: list[str] | None = None,
    cols: int = 4,
    title: str = "",
) -> str:
    """Render a grid of composite images into one contact-sheet PNG.

    Args:
        images: List of (size, size, 3) RGB arrays.
        path: Output PNG path.
        labels: Optional per-image caption (e.g. the seed).
        cols: Number of columns in the grid.
        title: Overall sheet title.
    """
    if plt is None:
        raise ImportError("matplotlib is required for rendering")
    n = len(images)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.2 * rows), dpi=90)
    flat = np.atleast_1d(axes).reshape(-1)
    for i, ax in enumerate(flat):
        if i < n:
            ax.imshow(images[i], interpolation="nearest")
            cap = labels[i] if labels else str(i)
            ax.set_title(cap, fontsize=9)
        else:
            ax.axis("off")
        ax.set_xticks([])
        ax.set_yticks([])
    if title:
        fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path
