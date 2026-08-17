"""Map-content toolkit templates.

These are the "quick, interesting content" templates that let a map author drop
a self-contained feature into a region with a single call:

  FAUNA_SCATTER        – Weighted scatter of wild animals (herds + predators).
  BERRY_BUSH           – Even scatter of forage / fruit bushes (berry patches).
  BANDIT_CAMP          – Small hostile camp: dirt patch, bonfire, tent ring, bandits.
  SNOWY_MOUNTAIN_RANGE – Elongated ridgeline of snow terrain + snow mountains + elevation.
  LUSH_FOREST          – Dense mixed forest with berry bushes, fauna, and clearings.

Design notes
------------
* **Determinism.** Every template draws its randomness from the ``MapManager``'s
  seeded RNG (``map_manager.rng``) and, where a NumPy sampler is used, from a
  ``numpy.random.Generator`` seeded with the same ``map_manager.seed``. A given
  seed therefore always produces the same map, which is what the golden-seed
  regression tests and the contact-sheet renderer rely on.

* **Direct placement.** These templates place objects with
  ``map_manager.get_map_layer(...).set_point(...)`` rather than the clustering
  ``place_groups`` placer. That gives precise, non-overlapping, fully
  deterministic control (the group placer uses the *global* ``random`` module and
  is a clustering tool, not a fill).

* **Region awareness.** Every placement is clamped to the caller-selected
  ``PointCollection`` via ``check_point_exists`` so the content never bleeds
  outside the region the author chose.

All templates are ``GAIA``-owned by default and are registered automatically when
this module is imported (see ``templates/__init__.py``).
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.utils.sampling import jittered_grid, poisson_disk


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _np_rng(map_manager: IMapManager) -> np.random.Generator:
    """Return a NumPy generator seeded identically to the map manager.

    Falls back to a non-deterministic generator when the manager has no seed,
    mirroring the behaviour of ``map_manager.rng``.
    """
    return np.random.default_rng(getattr(map_manager, "seed", None))


def _region_bounds(
    point_collection: PointCollection,
) -> Tuple[int, int, int, int]:
    """Return ``(min_x, min_y, max_x, max_y)`` of the region (inclusive)."""
    pts = point_collection.get_point_list()
    return (
        min(p[0] for p in pts),
        min(p[1] for p in pts),
        max(p[0] for p in pts),
        max(p[1] for p in pts),
    )


# ---------------------------------------------------------------------------
# Fauna scatter
# ---------------------------------------------------------------------------

@register_template(TemplateType.FAUNA_SCATTER)
class FaunaScatterTemplate(AbstractTemplate):
    """Weighted scatter of wild animals: grazing herds plus lone predators.

    Herd species are placed in small clusters (a Poisson-disk-spaced centre with
    a Gaussian scatter of a few members around it); predators are placed
    sparsely and singly.  The result reads as a natural wildlife population
    rather than a uniform grid.

    Keyword args:
        herd_count (int): Number of herd clusters.  Default ``6``.
        predator_count (int): Number of lone predators.  Default ``3``.
        herd_size (tuple[int, int]): Inclusive (min, max) members per herd.
            Default ``(3, 6)``.
    """

    def __init__(
        self,
        name: str = "Fauna Scatter",
        description: str = "Scatters wild animal herds and lone predators",
    ) -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs,
    ) -> PointCollection:
        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        herd_count: int = kwargs.get("herd_count", 6)
        predator_count: int = kwargs.get("predator_count", 3)
        herd_size: Tuple[int, int] = kwargs.get("herd_size", (3, 6))

        rng = map_manager.rng
        np_rng = _np_rng(map_manager)
        size = map_manager.map.size
        min_x, min_y, max_x, max_y = _region_bounds(point_collection)
        unit_layer = map_manager.get_map_layer(MapLayerType.UNIT)

        def place(x: float, y: float, obj: object) -> None:
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < size and 0 <= yi < size and point_collection.check_point_exists((xi, yi)):
                unit_layer.set_point((xi, yi), obj, player_id)

        herd_pool = [
            UnitInfo.DEER,
            UnitInfo.GOAT,
            UnitInfo.SHEEP,
            UnitInfo.PIG,
            UnitInfo.WILD_BOAR,
        ]
        # Evenly spaced herd centres, then a small Gaussian cluster around each.
        centers = poisson_disk(
            min_x, min_y, max_x + 1, max_y + 1,
            min_dist=12, max_points=herd_count, rng=np_rng,
        )
        for i, (cx, cy) in enumerate(centers):
            species = herd_pool[i % len(herd_pool)]
            for _ in range(rng.randint(*herd_size)):
                place(cx + rng.gauss(0, 3.0), cy + rng.gauss(0, 3.0), species)

        predator_pool = [UnitInfo.WOLF, UnitInfo.BEAR, UnitInfo.DIRE_WOLF]
        for i in range(predator_count):
            place(
                rng.randint(min_x, max_x),
                rng.randint(min_y, max_y),
                predator_pool[i % len(predator_pool)],
            )

        return point_collection


# ---------------------------------------------------------------------------
# Berry bush
# ---------------------------------------------------------------------------

@register_template(TemplateType.BERRY_BUSH)
class BerryBushTemplate(AbstractTemplate):
    """Even scatter of forage / fruit bushes (a berry patch).

    Uses a jittered grid so bushes are spread evenly across the region with
    organic irregularity, mixing several bush varieties for visual variety.

    Keyword args:
        density (float): Approximate fraction of tiles that receive a bush.
            Default ``0.02`` (a bush roughly every 7 tiles).
    """

    def __init__(
        self,
        name: str = "Berry Bush",
        description: str = "Scatters forage and fruit bushes across a region",
    ) -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs,
    ) -> PointCollection:
        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        density: float = kwargs.get("density", 0.02)
        rng = map_manager.rng
        np_rng = _np_rng(map_manager)
        size = map_manager.map.size
        min_x, min_y, max_x, max_y = _region_bounds(point_collection)
        unit_layer = map_manager.get_map_layer(MapLayerType.UNIT)

        bush_pool = [
            OtherInfo.FORAGE_BUSH,
            OtherInfo.FRUIT_BUSH,
            OtherInfo.BUSH_A,
            OtherInfo.BUSH_B,
            OtherInfo.BUSH_C,
        ]
        cell = max(2, int(math.sqrt(1.0 / max(density, 1e-6))))
        grid = jittered_grid(
            min_x, min_y, max_x + 1, max_y + 1,
            cell=cell, jitter=0.4, rng=np_rng,
        )
        for (x, y) in grid:
            if 0 <= x < size and 0 <= y < size and point_collection.check_point_exists((x, y)):
                unit_layer.set_point((x, y), bush_pool[rng.randrange(len(bush_pool))], player_id)

        return point_collection


# ---------------------------------------------------------------------------
# Bandit camp
# ---------------------------------------------------------------------------

@register_template(TemplateType.BANDIT_CAMP)
class BanditCampTemplate(AbstractTemplate):
    """A small hostile camp: dirt patch, central bonfire, a ring of tents,
    and a handful of bandits milling around.

    Layout (concentric):
    1. Circular ``DIRT_1`` terrain patch.
    2. A single ``BONFIRE`` at the centre.
    3. A ring of tents (``TENT_A``–``TENT_E``) around the fire.
    4. Bandit units scattered between the fire and the tents.

    Keyword args:
        center_point (tuple[int, int]): Camp centre.  Defaults to the region
            centroid.
        size (int): Camp radius in tiles.  Default ``10``.
        tents (int): Number of tents in the ring.  Default ``5``.
        bandits (int): Number of bandit units.  Default ``6``.
    """

    def __init__(
        self,
        name: str = "Bandit Camp",
        description: str = "Creates a small hostile bandit camp",
    ) -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs,
    ) -> PointCollection:
        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        center: Tuple[int, int] = kwargs.get(
            "center_point", point_collection.get_average_point_position()
        )
        radius: int = kwargs.get("size", 10)
        n_tents: int = kwargs.get("tents", 5)
        n_bandits: int = kwargs.get("bandits", 6)

        cx, cy = center
        size = map_manager.map.size
        rng = map_manager.rng
        terrain_layer = map_manager.get_map_layer(MapLayerType.TERRAIN)
        unit_layer = map_manager.get_map_layer(MapLayerType.UNIT)

        def in_region(x: int, y: int) -> bool:
            return 0 <= x < size and 0 <= y < size and point_collection.check_point_exists((x, y))

        # 1. Circular dirt patch.
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                if in_region(x, y) and (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                    terrain_layer.set_point((x, y), TerrainId.DIRT_1, PlayerId.GAIA)

        # 2. Central bonfire.
        if in_region(cx, cy):
            unit_layer.set_point((cx, cy), OtherInfo.BONFIRE, PlayerId.GAIA)

        # 3. Ring of tents.
        tent_pool = [
            BuildingInfo.TENT_A,
            BuildingInfo.TENT_B,
            BuildingInfo.TENT_C,
            BuildingInfo.TENT_D,
            BuildingInfo.TENT_E,
        ]
        for i in range(n_tents):
            angle = 2 * math.pi * i / n_tents + rng.uniform(-0.2, 0.2)
            tx = int(round(cx + (radius - 3) * math.cos(angle)))
            ty = int(round(cy + (radius - 3) * math.sin(angle)))
            if in_region(tx, ty):
                unit_layer.set_point((tx, ty), tent_pool[i % len(tent_pool)], PlayerId.GAIA)

        # 4. Bandits scattered between the fire and the tents.
        for _ in range(n_bandits):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(2, max(3, radius - 1))
            bx = int(round(cx + dist * math.cos(angle)))
            by = int(round(cy + dist * math.sin(angle)))
            if in_region(bx, by):
                unit_layer.set_point((bx, by), UnitInfo.BANDIT, PlayerId.GAIA)

        return point_collection


# ---------------------------------------------------------------------------
# Snowy mountain range
# ---------------------------------------------------------------------------

@register_template(TemplateType.SNOWY_MOUNTAIN_RANGE)
class SnowyMountainRangeTemplate(AbstractTemplate):
    """An elongated snow-mountain ridgeline.

    The region's long axis is treated as the ridge: elevation peaks along the
    ridge and falls off toward the flanks, snow terrain covers the whole range,
    and snow-mountain objects are scattered on the high ground.  Feed it an
    elongated (non-square) region for the best ridgeline shape.

    Keyword args:
        max_elevation (int): Peak elevation at the ridge (0–7).  Default ``6``.
    """

    def __init__(
        self,
        name: str = "Snowy Mountain Range",
        description: str = "Creates an elongated snow-mountain ridgeline",
    ) -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs,
    ) -> PointCollection:
        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        max_elevation: int = max(1, min(7, int(kwargs.get("max_elevation", 6))))
        cx, cy = point_collection.get_average_point_position()
        rng = map_manager.rng
        terrain_layer = map_manager.get_map_layer(MapLayerType.TERRAIN)
        unit_layer = map_manager.get_map_layer(MapLayerType.UNIT)
        elev_layer = map_manager.get_map_layer(MapLayerType.ELEVATION)

        min_x, min_y, max_x, max_y = _region_bounds(point_collection)
        # Ridge runs along the long axis of the region.
        if (max_x - min_x) >= (max_y - min_y):
            half_width = max((max_y - min_y) / 2.0, 1.0)

            def ridge_dist(x: int, y: int) -> float:
                return abs(y - cy)
        else:
            half_width = max((max_x - min_x) / 2.0, 1.0)

            def ridge_dist(x: int, y: int) -> float:
                return abs(x - cx)

        mountain_pool = [
            OtherInfo.SNOW_MOUNTAIN_1,
            OtherInfo.SNOW_MOUNTAIN_2,
            OtherInfo.SNOW_MOUNTAIN_3,
        ]
        for (x, y) in pts:
            d = ridge_dist(x, y)
            elevation = max(0, int(max_elevation * (1.0 - d / half_width)))
            elev_layer.set_point((x, y), elevation, PlayerId.GAIA)
            terrain_layer.set_point((x, y), TerrainId.SNOW, PlayerId.GAIA)
            # Snow-mountain objects on the high ground near the ridge.
            if elevation >= 3 and rng.random() < 0.5:
                unit_layer.set_point(
                    (x, y), mountain_pool[rng.randrange(len(mountain_pool))], PlayerId.GAIA
                )

        return point_collection


# ---------------------------------------------------------------------------
# Lush forest
# ---------------------------------------------------------------------------

@register_template(TemplateType.LUSH_FOREST)
class LushForestTemplate(AbstractTemplate):
    """A dense mixed forest with berry bushes, a little fauna, and clearings.

    Trees are laid out on a jittered grid (dense, mixed species) with a few
    circular clearings left open; berry bushes and a handful of deer are
    scattered through the undergrowth.

    Keyword args:
        tree_density (float): Approximate fraction of tiles that receive a
            tree.  Default ``0.15``.
        clearings (int): Number of open clearings.  Default ``3``.
    """

    def __init__(
        self,
        name: str = "Lush Forest",
        description: str = "Creates a dense mixed forest with clearings",
    ) -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs,
    ) -> PointCollection:
        pts = point_collection.get_point_list()
        if not pts:
            return point_collection

        tree_density: float = kwargs.get("tree_density", 0.15)
        n_clearings: int = kwargs.get("clearings", 3)
        rng = map_manager.rng
        np_rng = _np_rng(map_manager)
        size = map_manager.map.size
        min_x, min_y, max_x, max_y = _region_bounds(point_collection)
        unit_layer = map_manager.get_map_layer(MapLayerType.UNIT)

        # Open clearings (no trees inside these circles).
        clearing_radius = 6
        clearing_centers = [
            (rng.randint(min_x, max_x), rng.randint(min_y, max_y))
            for _ in range(n_clearings)
        ]

        def in_clearing(x: int, y: int) -> bool:
            return any(
                (x - ccx) ** 2 + (y - ccy) ** 2 <= clearing_radius ** 2
                for (ccx, ccy) in clearing_centers
            )

        tree_pool = [
            OtherInfo.TREE_OAK,
            OtherInfo.TREE_OAK_FOREST,
            OtherInfo.TREE_PINE_FOREST,
            OtherInfo.TREE_OAK_AUTUMN,
        ]
        cell = max(2, int(math.sqrt(1.0 / max(tree_density, 1e-6))))
        for (x, y) in jittered_grid(
            min_x, min_y, max_x + 1, max_y + 1, cell=cell, jitter=0.5, rng=np_rng
        ):
            if 0 <= x < size and 0 <= y < size and point_collection.check_point_exists((x, y)) \
                    and not in_clearing(x, y):
                unit_layer.set_point((x, y), tree_pool[rng.randrange(len(tree_pool))], player_id)

        # Berry bushes in the undergrowth (sparser than trees).
        berry_pool = [OtherInfo.FORAGE_BUSH, OtherInfo.FRUIT_BUSH, OtherInfo.BUSH_A]
        for (x, y) in jittered_grid(
            min_x, min_y, max_x + 1, max_y + 1, cell=cell * 2, jitter=0.5, rng=np_rng
        ):
            if 0 <= x < size and 0 <= y < size and point_collection.check_point_exists((x, y)):
                unit_layer.set_point((x, y), berry_pool[rng.randrange(len(berry_pool))], player_id)

        # A little fauna.
        for _ in range(8):
            fx, fy = rng.randint(min_x, max_x), rng.randint(min_y, max_y)
            if point_collection.check_point_exists((fx, fy)):
                unit_layer.set_point((fx, fy), UnitInfo.DEER, player_id)

        return point_collection
