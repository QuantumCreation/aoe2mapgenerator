"""Nature area templates: ponds, rivers, pine forests, winter landscapes,
desert biomes, savannah, rainforest, and Mediterranean woodland.

Template overview
-----------------
Primitive water bodies (compose well with other templates):
  POND            – Circular freshwater pool (shallows terrain + fish + reeds).
  RIVER_SEGMENT   – Fills the selected region with a flowing river
                    (water_shallow terrain + fish + reeds).

Forest variants:
  PINE_FOREST     – Coniferous pine forest (trees + deer + wolves + rocks).

Full biome composites:
  WINTER_LANDSCAPE – Snow terrain + snow pine trees + frozen pond (ice terrain)
                     + arctic fauna (wolves, snow leopards, bears).
  DESERT          – Desert sand terrain + palm trees + cacti + desert fauna.
  DESERT_OASIS    – Desert biome with a central freshwater oasis (fish).
  SAVANNAH        – Dry grassland with acacia/baobab trees + savannah fauna.
  RAINFOREST      – Dense jungle with exotic vegetation + rainforest fauna.
  MEDITERRANEAN   – Mediterranean grassland with mixed woodland + temperate fauna.

All templates consume the caller-selected ``PointCollection`` and are
``GAIA``-owned by default.  They are registered automatically when this module
is imported; add it to ``templates/__init__.py`` to activate registration.
"""

import math
import random
from typing import Tuple

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.common.enums.enum import (
    MapLayerType,
    ObjectsFish,
    ObjectsAnimalsArctic,
    ObjectsAnimalsDesert,
    ObjectsAnimalsSavannah,
    ObjectsAnimalsRainforest,
)
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.placer_configs import PlaceGroupsConfig
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _place_fish(
    map_manager: IMapManager,
    water_coll: PointCollection,
    fish_pool: list,
    n_species: int = 2,
    groups_density: float = 0.01,
    group_size_range: Tuple[int, int] = (2, 4),
    clumping: int = 3,
) -> None:
    """Scatter random fish species across *water_coll*.

    Args:
        map_manager: Active map manager.
        water_coll: Tiles where fish can be placed (water terrain tiles).
        fish_pool: List of OtherInfo fish values to sample from.
        n_species: How many distinct fish species to place.
        groups_density: Density passed to PlaceGroupsConfig.
        group_size_range: (min, max) inclusive group size range.
        clumping: Tightness of fish clusters.
    """
    selected = random.sample(fish_pool, k=min(n_species, len(fish_pool)))
    for fish in selected:
        config = PlaceGroupsConfig(
            point_collection=water_coll,
            map_layer_type=MapLayerType.UNIT,
            object_type=fish,
            player_id=PlayerId.GAIA,
            groups_density=groups_density,
            group_size=random.randint(*group_size_range),
            clumping=clumping,
        )
        map_manager.group_placer.place_groups(config)


def _place_terrain_fill(
    map_manager: IMapManager,
    coll: PointCollection,
    terrain: TerrainId,
    groups: int = 1,
    group_size: int = 500,
    clumping: int = 4,
    start_point: Tuple[int, int] | None = None,
) -> None:
    """Fill *coll* with *terrain* in one large group."""
    cfg = PlaceGroupsConfig(
        point_collection=coll,
        map_layer_type=MapLayerType.TERRAIN,
        object_type=terrain,
        player_id=PlayerId.GAIA,
        groups=groups,
        group_size=group_size,
        clumping=clumping,
        start_point=start_point,
    )
    map_manager.group_placer.place_groups(cfg)


def _place_objects_scattered(
    map_manager: IMapManager,
    coll: PointCollection,
    object_type: object,
    player_id: PlayerId = PlayerId.GAIA,
    map_layer: MapLayerType = MapLayerType.UNIT,
    groups_density: float = 0.002,
    group_size: int = 5,
    clumping: int = 5,
) -> None:
    """Convenience wrapper for scattered group placement."""
    cfg = PlaceGroupsConfig(
        point_collection=coll,
        map_layer_type=map_layer,
        object_type=object_type,
        player_id=player_id,
        groups_density=groups_density,
        group_size=group_size,
        clumping=clumping,
    )
    map_manager.group_placer.place_groups(cfg)


def _place_water_body(
    map_manager: IMapManager,
    base_coll: PointCollection,
    center: Tuple[int, int],
    radius: int,
    terrain: TerrainId,
    fish_pool: list,
    n_fish_species: int = 2,
    add_reeds: bool = True,
) -> PointCollection:
    """Create a circular water body and populate it with fish and optional reeds.

    Returns the water ``PointCollection`` for further use.
    """
    water_coll = base_coll.copy()
    water_coll.filter_by_distance(center, distance=radius, edit_in_place=True)

    if len(water_coll.get_point_list()) == 0:
        return water_coll

    # Save a copy for fish placement BEFORE terrain fill consumes all points.
    # place_groups calls point_collection.remove_point() for each placed object,
    # so the collection will be empty after terrain fill.
    fish_coll = water_coll.copy()

    # Terrain fill (depletes water_coll)
    _place_terrain_fill(
        map_manager, water_coll, terrain,
        groups=1, group_size=max(len(water_coll.get_point_list()), 20),
        clumping=4, start_point=center,
    )

    # Fish — use the pre-depletion copy
    _place_fish(map_manager, fish_coll, fish_pool, n_species=n_fish_species)

    # Shore reeds just outside the water circle
    if add_reeds:
        shore_r = radius + 3
        shore_coll = base_coll.copy()
        shore_coll.filter_by_distance(center, distance=shore_r, edit_in_place=True)
        _place_objects_scattered(
            map_manager, shore_coll, OtherInfo.TREE_REEDS,
            groups_density=0.008, group_size=random.randint(2, 4), clumping=4,
        )

    return water_coll


# ---------------------------------------------------------------------------
# Pond
# ---------------------------------------------------------------------------

@register_template(TemplateType.POND)
class PondTemplate(AbstractTemplate):
    """Freshwater pond: shallows terrain + fish + reeds.

    Keyword args (via ``TemplateConfig`` or direct kwargs):
        center_point (tuple[int, int]): Centre of the pond.  Defaults to the
            centroid of *point_collection*.
        size (int): Radius of the pond in tiles.  Default ``8``.
    """

    def __init__(
        self,
        name: str = "Pond",
        description: str = "Creates a freshwater pond with fish and reeds",
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
        center: Tuple[int, int] = kwargs.get(
            "center_point", point_collection.get_average_point_position()
        )
        radius: int = kwargs.get("size", 8)

        freshwater_fish = [
            OtherInfo.FISH_PERCH,
            OtherInfo.FISH_SALMON,
            OtherInfo.SHORE_FISH,
            OtherInfo.FISH_DORADO,
            OtherInfo.BOX_TURTLES,
        ]
        _place_water_body(
            map_manager, point_collection, center, radius,
            terrain=TerrainId.SHALLOWS,
            fish_pool=freshwater_fish,
            n_fish_species=3,
            add_reeds=True,
        )
        return point_collection


# ---------------------------------------------------------------------------
# River segment
# ---------------------------------------------------------------------------

@register_template(TemplateType.RIVER_SEGMENT)
class RiverSegmentTemplate(AbstractTemplate):
    """River segment: fills the selected region with flowing water + fish.

    The caller selects the river channel; this template fills it with
    ``WATER_SHALLOW`` terrain and populates it with fish and shore reeds.

    No extra keyword args are required — the template works entirely on the
    provided *point_collection*.
    """

    def __init__(
        self,
        name: str = "River Segment",
        description: str = "Fills the selected region with a flowing river",
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
        if len(point_collection.get_point_list()) == 0:
            return point_collection

        # Fill the selected region with shallow water
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.WATER_SHALLOW,
            groups=1, group_size=max(len(point_collection.get_point_list()), 30),
            clumping=3,
        )

        # Fish — rivers carry salmon, tuna, and dorado
        river_fish = [
            OtherInfo.FISH_SALMON,
            OtherInfo.FISH_TUNA,
            OtherInfo.FISH_DORADO,
            OtherInfo.FISH_SNAPPER,
            OtherInfo.SHORE_FISH,
        ]
        _place_fish(
            map_manager, point_collection.copy(), river_fish,
            n_species=3, groups_density=0.008, group_size_range=(2, 5),
        )

        # Shore reeds along the river banks
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_REEDS,
            groups_density=0.006, group_size=3, clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.PLANT_RAINFOREST,
            groups_density=0.003, group_size=2, clumping=3,
        )

        return point_collection


# ---------------------------------------------------------------------------
# Pine forest
# ---------------------------------------------------------------------------

@register_template(TemplateType.PINE_FOREST)
class PineForestTemplate(AbstractTemplate):
    """Coniferous pine forest with trees, deer, wolves, and rocks.

    Keyword args:
        groups_density (float): Fraction of tiles used as tree-group seeds.
            Default ``0.01``.
        group_size (int): Trees per group.  Default ``12``.
        clumping (int): Tree cluster tightness.  Default ``5``.
    """

    def __init__(
        self,
        name: str = "Pine Forest",
        description: str = "Creates a coniferous pine forest",
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
        groups_density: float = kwargs.get("groups_density", 0.01)
        group_size: int = kwargs.get("group_size", 12)
        clumping: int = kwargs.get("clumping", 5)

        # Primary pine trees
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_PINE_FOREST,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )

        # Secondary italian pine variety for visual variety
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_ITALIAN_PINE,
            groups_density=groups_density * 0.3,
            group_size=max(4, group_size // 3),
            clumping=clumping,
        )

        # Undergrowth
        for plant in (OtherInfo.PLANT_UNDERBRUSH, OtherInfo.PLANT_SHRUB_GREEN, OtherInfo.PLANT):
            _place_objects_scattered(
                map_manager, point_collection.copy(), plant,
                map_layer=MapLayerType.DECOR,
                groups_density=0.002, group_size=random.randint(2, 4), clumping=4,
            )

        # Rock formations
        for rock in (OtherInfo.ROCK_1, OtherInfo.ROCK_2):
            _place_objects_scattered(
                map_manager, point_collection.copy(), rock,
                groups_density=0.0005, group_size=1, clumping=2,
            )

        # Fauna: deer herds (primary), wolves (predators), bears (solitary)
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.DEER,
            groups_density=0.001, group_size=random.randint(3, 5), clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.WOLF,
            groups_density=0.0005, group_size=random.randint(2, 4), clumping=5,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.BEAR,
            groups_density=0.0003, group_size=random.randint(1, 2), clumping=3,
        )

        # Resources: forage bushes and a hint of stone/ore
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.FORAGE_BUSH,
            groups_density=0.0005, group_size=random.randint(2, 4), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.STONE_MINE,
            groups_density=0.0002, group_size=1, clumping=2,
        )

        return point_collection


# ---------------------------------------------------------------------------
# Winter landscape
# ---------------------------------------------------------------------------

@register_template(TemplateType.WINTER_LANDSCAPE)
class WinterLandscapeTemplate(AbstractTemplate):
    """Composite winter biome: snow terrain, snow pine trees, frozen pond,
    and arctic fauna.

    Layout:
    1. Snow terrain across the whole region.
    2. Snow pine / snow oak trees scattered at configurable density.
    3. Snow undergrowth decor.
    4. Frozen pond: small ICE terrain circle + arctic fish.
    5. Arctic animals: wolves, snow leopards, bears.
    6. Rock formations dusted across the region.

    Keyword args:
        groups_density (float): Tree density.  Default ``0.01``.
        group_size (int): Trees per group.  Default ``10``.
        clumping (int): Tree cluster tightness.  Default ``5``.
        center_point (tuple[int, int]): Used to anchor the frozen pond;
            defaults to centroid of *point_collection*.
        size (int): Radius of the frozen pond inset from the region.
            Default ``6``.
    """

    def __init__(
        self,
        name: str = "Winter Landscape",
        description: str = "Snow biome with frozen pond and arctic fauna",
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
        groups_density: float = kwargs.get("groups_density", 0.01)
        group_size: int = kwargs.get("group_size", 10)
        clumping: int = kwargs.get("clumping", 5)
        center: Tuple[int, int] = kwargs.get(
            "center_point", point_collection.get_average_point_position()
        )
        pond_radius: int = kwargs.get("size", 6)

        cx, cy = center

        # 1. Snow terrain base
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.SNOW,
            groups=1, group_size=max(len(point_collection.get_point_list()), 50),
            clumping=3,
        )

        # 2. Snow pine trees
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_SNOW_PINE,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )
        # Mix in snow oak for variety
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_OAK_AUTUMN_SNOW,
            groups_density=groups_density * 0.35,
            group_size=max(3, group_size // 3),
            clumping=clumping,
        )

        # 3. Snow undergrowth / decor
        for obj in (OtherInfo.PLANT_DEAD, OtherInfo.ROCK_1, OtherInfo.STUMP):
            _place_objects_scattered(
                map_manager, point_collection.copy(), obj,
                map_layer=MapLayerType.DECOR,
                groups_density=0.001, group_size=random.randint(1, 3), clumping=3,
            )

        # 4. Frozen pond — offset SW from center so it isn't smack in the middle
        pond_cx = int(cx - 0.30 * pond_radius * 2)
        pond_cy = int(cy + 0.30 * pond_radius * 2)
        pond_center = (pond_cx, pond_cy)
        arctic_fish = [OtherInfo.FISH_PERCH, OtherInfo.FISH_SALMON, OtherInfo.SHORE_FISH]
        _place_water_body(
            map_manager, point_collection, pond_center, pond_radius,
            terrain=TerrainId.ICE,
            fish_pool=arctic_fish,
            n_fish_species=2,
            add_reeds=False,  # no reeds on a frozen pond
        )

        # 5. Arctic animals
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.WOLF,
            groups_density=0.001, group_size=random.randint(2, 4), clumping=5,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.SNOW_LEOPARD,
            groups_density=0.0005, group_size=random.randint(1, 2), clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.BEAR,
            groups_density=0.0004, group_size=1, clumping=3,
        )

        # 6. Rock formations
        for rock in (OtherInfo.ROCK_2, OtherInfo.ROCK_FORMATION_1):
            _place_objects_scattered(
                map_manager, point_collection.copy(), rock,
                groups_density=0.0004, group_size=1, clumping=2,
            )

        return point_collection


# ---------------------------------------------------------------------------
# Desert
# ---------------------------------------------------------------------------

@register_template(TemplateType.DESERT)
class DesertTemplate(AbstractTemplate):
    """Arid desert biome: sand terrain, sparse palms, cacti, and desert animals.

    Keyword args:
        groups_density (float): Vegetation density.  Default ``0.005``.
        group_size (int): Objects per group.  Default ``6``.
        clumping (int): Cluster tightness.  Default ``4``.
    """

    def __init__(
        self,
        name: str = "Desert",
        description: str = "Arid desert with palms, cacti, and desert fauna",
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
        groups_density: float = kwargs.get("groups_density", 0.005)
        group_size: int = kwargs.get("group_size", 6)
        clumping: int = kwargs.get("clumping", 4)

        # 1. Sand terrain
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.DESERT_SAND,
            groups=1, group_size=max(len(point_collection.get_point_list()), 50),
            clumping=3,
        )

        # 2. Palm trees (sparse — this is a desert, not a forest)
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_PALM_FOREST,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )

        # 3. Cactus clusters
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.CACTUS,
            groups_density=groups_density * 0.6,
            group_size=random.randint(2, 4), clumping=3,
        )

        # 4. Desert decor: rocks, dead plants, formations
        for obj in (OtherInfo.ROCK_1, OtherInfo.ROCK_2, OtherInfo.ROCK_FORMATION_1,
                    OtherInfo.ROCK_FORMATION_2, OtherInfo.PLANT_DEAD):
            _place_objects_scattered(
                map_manager, point_collection.copy(), obj,
                map_layer=MapLayerType.DECOR,
                groups_density=0.001, group_size=random.randint(1, 3), clumping=3,
            )

        # 5. Desert fauna
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.WILD_BACTRIAN_CAMEL,
            groups_density=0.0005, group_size=random.randint(2, 4), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.WILD_CAMEL,
            groups_density=0.0004, group_size=random.randint(2, 3), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.LION,
            groups_density=0.0003, group_size=random.randint(1, 2), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.VULTURE,
            groups_density=0.0003, group_size=random.randint(1, 3), clumping=3,
        )

        return point_collection


# ---------------------------------------------------------------------------
# Desert oasis
# ---------------------------------------------------------------------------

@register_template(TemplateType.DESERT_OASIS)
class DesertOasisTemplate(AbstractTemplate):
    """Desert biome with a central freshwater oasis.

    Combines a full ``DesertTemplate`` with a circular shallows pool at the
    centre, surrounded by date palms and populated with freshwater fish.

    Keyword args:
        groups_density (float): Background vegetation density.  Default ``0.004``.
        group_size (int): Objects per group.  Default ``5``.
        clumping (int): Cluster tightness.  Default ``4``.
        center_point (tuple[int, int]): Centre of the oasis pool.  Defaults to
            the centroid of *point_collection*.
        size (int): Radius of the oasis pool in tiles.  Default ``10``.
    """

    def __init__(
        self,
        name: str = "Desert Oasis",
        description: str = "Desert biome with a central freshwater oasis",
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
        groups_density: float = kwargs.get("groups_density", 0.004)
        group_size: int = kwargs.get("group_size", 5)
        clumping: int = kwargs.get("clumping", 4)
        center: Tuple[int, int] = kwargs.get(
            "center_point", point_collection.get_average_point_position()
        )
        oasis_radius: int = kwargs.get("size", 10)

        # Step 1: Desert background (reuse DesertTemplate logic)
        DesertTemplate.generate(
            map_manager, point_collection, player_id=player_id,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )

        # Step 2: Central oasis pool with shallows terrain
        oasis_fish = [
            OtherInfo.FISH_DORADO,
            OtherInfo.FISH_PERCH,
            OtherInfo.SHORE_FISH,
            OtherInfo.BOX_TURTLES,
        ]
        _place_water_body(
            map_manager, point_collection, center, oasis_radius,
            terrain=TerrainId.SHALLOWS_AZURE,
            fish_pool=oasis_fish,
            n_fish_species=3,
            add_reeds=False,
        )

        # Step 3: Date palms ring around the oasis
        palm_ring_coll = point_collection.copy()
        inner_r = max(1, oasis_radius - 2)
        # Keep tiles between oasis radius and oasis radius + 8
        palm_ring_coll.filter_by_distance(center, distance=oasis_radius + 8, edit_in_place=True)
        _place_objects_scattered(
            map_manager, palm_ring_coll, OtherInfo.TREE_PALM_FOREST,
            groups_density=0.03, group_size=random.randint(3, 6), clumping=4,
        )

        # Step 4: Lush vegetation at the oasis edge
        for plant in (OtherInfo.PLANT_BUSH_GREEN, OtherInfo.PLANT_SHRUB_GREEN):
            edge_coll = point_collection.copy()
            edge_coll.filter_by_distance(center, distance=oasis_radius + 6, edit_in_place=True)
            _place_objects_scattered(
                map_manager, edge_coll, plant,
                map_layer=MapLayerType.DECOR,
                groups_density=0.005, group_size=2, clumping=3,
            )

        # Step 5: Camels gathering at the oasis
        camel_coll = point_collection.copy()
        camel_coll.filter_by_distance(center, distance=oasis_radius + 12, edit_in_place=True)
        _place_objects_scattered(
            map_manager, camel_coll, UnitInfo.WILD_CAMEL,
            groups_density=0.002, group_size=random.randint(3, 5), clumping=4,
        )

        return point_collection


# ---------------------------------------------------------------------------
# Savannah
# ---------------------------------------------------------------------------

@register_template(TemplateType.SAVANNAH)
class SavannahTemplate(AbstractTemplate):
    """African savannah: dry grassland, sparse acacia/baobab trees, and savannah fauna.

    Keyword args:
        groups_density (float): Tree density.  Default ``0.003``.
        group_size (int): Trees per group.  Default ``4``.
        clumping (int): Cluster tightness.  Default ``3``.
    """

    def __init__(
        self,
        name: str = "Savannah",
        description: str = "Dry African savannah with acacia trees and wildlife",
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
        groups_density: float = kwargs.get("groups_density", 0.003)
        group_size: int = kwargs.get("group_size", 4)
        clumping: int = kwargs.get("clumping", 3)

        # 1. Dry grass terrain
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.GRASS_DRY,
            groups=1, group_size=max(len(point_collection.get_point_list()), 50), clumping=3,
        )
        # Savannah dirt patches
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.DIRT_SAVANNAH,
            groups=4, group_size=20, clumping=2,
        )

        # 2. Acacia trees (very sparse — savannah is open)
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_ACACIA,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )

        # 3. Baobab trees (even sparser and solitary)
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_BAOBAB,
            groups_density=groups_density * 0.25,
            group_size=random.randint(1, 2), clumping=2,
        )

        # 4. Dry vegetation decor
        for obj in (OtherInfo.PLANT_DEAD, OtherInfo.PLANT_WEEDS,
                    OtherInfo.GRASS_PATCH_DRY):
            _place_objects_scattered(
                map_manager, point_collection.copy(), obj,
                map_layer=MapLayerType.DECOR,
                groups_density=0.002, group_size=random.randint(2, 4), clumping=3,
            )

        # 5. Savannah fauna — large herds + predators
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.ZEBRA,
            groups_density=0.001, group_size=random.randint(4, 7), clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.OSTRICH,
            groups_density=0.0007, group_size=random.randint(3, 5), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.RHINOCEROS,
            groups_density=0.0004, group_size=random.randint(1, 2), clumping=2,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.LION,
            groups_density=0.0005, group_size=random.randint(2, 3), clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.IBEX,
            groups_density=0.0006, group_size=random.randint(3, 5), clumping=3,
        )

        # 6. Resources: gold glints under the rocks, stone outcrops
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.GOLD_MINE,
            groups_density=0.0002, group_size=1, clumping=2,
        )

        return point_collection


# ---------------------------------------------------------------------------
# Rainforest
# ---------------------------------------------------------------------------

@register_template(TemplateType.RAINFOREST)
class RainforestTemplate(AbstractTemplate):
    """Dense tropical rainforest with exotic vegetation and fauna.

    Keyword args:
        groups_density (float): Tree density.  Default ``0.015``.
        group_size (int): Trees per group.  Default ``14``.
        clumping (int): Cluster tightness.  Default ``6``.
    """

    def __init__(
        self,
        name: str = "Rainforest",
        description: str = "Dense tropical rainforest with exotic flora and fauna",
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
        groups_density: float = kwargs.get("groups_density", 0.015)
        group_size: int = kwargs.get("group_size", 14)
        clumping: int = kwargs.get("clumping", 6)

        # 1. Jungle terrain base
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.GRASS_JUNGLE,
            groups=1, group_size=max(len(point_collection.get_point_list()), 50), clumping=3,
        )

        # 2. Rainforest canopy — dense and varied
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_RAINFOREST,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_JUNGLE,
            groups_density=groups_density * 0.5,
            group_size=max(4, group_size // 2), clumping=clumping,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_MANGROVE,
            groups_density=groups_density * 0.15,
            group_size=random.randint(4, 8), clumping=4,
        )

        # 3. Dense undergrowth
        for plant in (OtherInfo.PLANT_RAINFOREST, OtherInfo.PLANT_BUSH_GREEN,
                      OtherInfo.PLANT_SHRUB_GREEN, OtherInfo.PLANT_UNDERBRUSH,
                      OtherInfo.PLANT_FLOWERS):
            _place_objects_scattered(
                map_manager, point_collection.copy(), plant,
                map_layer=MapLayerType.DECOR,
                groups_density=0.003, group_size=random.randint(2, 5), clumping=5,
            )

        # 4. Rainforest fauna
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.JAGUAR,
            groups_density=0.0005, group_size=random.randint(1, 2), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.MACAW,
            groups_density=0.001, group_size=random.randint(2, 4), clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.STORK,
            groups_density=0.0005, group_size=random.randint(1, 3), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.CROCODILE,
            groups_density=0.0003, group_size=random.randint(1, 2), clumping=2,
        )

        # 5. Fruit bushes hidden in the undergrowth
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.FRUIT_BUSH,
            groups_density=0.001, group_size=random.randint(2, 4), clumping=3,
        )

        return point_collection


# ---------------------------------------------------------------------------
# Mediterranean
# ---------------------------------------------------------------------------

@register_template(TemplateType.MEDITERRANEAN)
class MediterraneanTemplate(AbstractTemplate):
    """Mediterranean woodland: mixed olive, cypress, and oak trees with temperate fauna.

    Keyword args:
        groups_density (float): Tree density.  Default ``0.008``.
        group_size (int): Trees per group.  Default ``8``.
        clumping (int): Cluster tightness.  Default ``4``.
    """

    def __init__(
        self,
        name: str = "Mediterranean",
        description: str = "Mediterranean woodland with olive, cypress, and oak trees",
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
        groups_density: float = kwargs.get("groups_density", 0.008)
        group_size: int = kwargs.get("group_size", 8)
        clumping: int = kwargs.get("clumping", 4)

        # 1. Lush green terrain
        _place_terrain_fill(
            map_manager, point_collection.copy(), TerrainId.GRASS_2,
            groups=1, group_size=max(len(point_collection.get_point_list()), 50), clumping=3,
        )

        # 2. Mediterranean trees
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_OLIVE,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_CYPRESS,
            groups_density=groups_density * 0.4,
            group_size=max(3, group_size // 2), clumping=clumping,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.TREE_OAK,
            groups_density=groups_density * 0.3,
            group_size=max(3, group_size // 3), clumping=clumping,
        )

        # 3. Undergrowth and flowers
        for obj in (OtherInfo.BUSH_A, OtherInfo.BUSH_B, OtherInfo.PLANT_BUSH_GREEN,
                    OtherInfo.FLOWERS_1, OtherInfo.FLOWERS_2, OtherInfo.FLOWERS_3):
            _place_objects_scattered(
                map_manager, point_collection.copy(), obj,
                map_layer=MapLayerType.DECOR,
                groups_density=0.002, group_size=random.randint(2, 4), clumping=4,
            )

        # 4. Temperate fauna
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.DEER,
            groups_density=0.001, group_size=random.randint(3, 5), clumping=4,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.WILD_BOAR,
            groups_density=0.0005, group_size=random.randint(2, 3), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.BEAR,
            groups_density=0.0003, group_size=random.randint(1, 2), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), UnitInfo.HAWK,
            groups_density=0.0003, group_size=1, clumping=2,
        )

        # 5. Resources: fruit bushes, stone, gold
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.FORAGE_BUSH,
            groups_density=0.0005, group_size=random.randint(2, 4), clumping=3,
        )
        _place_objects_scattered(
            map_manager, point_collection.copy(), OtherInfo.STONE_MINE,
            groups_density=0.0002, group_size=1, clumping=2,
        )

        return point_collection
