"""MapManager — central façade for AoE2 map construction.

Provides a fluent API for building maps by composing placers, templates,
and the Voronoi zone generator.  All mutating methods return ``self`` to
support method chaining.

Typical usage::

    mm = MapManager(size=200)
    mm.place_groups(PlaceGroupsConfig(...))
    mm.write_map_and_save("my_map.aoe2scenario")
"""

import os
from typing import Any, List, Tuple

from AoE2ScenarioParser.datasets.players import PlayerId

import random as _random
from aoe2mapgenerator.common.constants.constants import (
    BASE_SCENARIO_NAME,
    BASE_SCENE_DIR_WINDOWS_WSL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PLAYER,
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.common.types import AOE2ObjectType, Point
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.scenario.scenario import Scenario
from aoe2mapgenerator.scenario.scenario_config import (
    PlayerConfig,
    ScenarioConfig,
    configure_scenario as _configure_scenario,
)
from aoe2mapgenerator.terrain.terrain import PerlinTerrainConfig, PerlinTerrainGenerator
from aoe2mapgenerator.templates.city_hybrid import CityTemplate  # noqa: F401 – registers via @register_template
from aoe2mapgenerator.templates.decor import OakForestTemplate, SnowForestTemplate
from aoe2mapgenerator.templates.fort import FortTemplate  # noqa: F401 – registers via @register_template
from aoe2mapgenerator.templates.palace import PalaceTemplate  # noqa: F401 – registers via @register_template
from aoe2mapgenerator.templates.village import VillageTemplate  # noqa: F401 – registers via @register_template
import aoe2mapgenerator.templates.nature  # noqa: F401 – side-effect: registers all nature templates
import aoe2mapgenerator.templates.missing_templates  # noqa: F401 – registers WALLS, ROAD, MINE, MOUNTAIN, CASTLE, RIVER
from aoe2mapgenerator.templates.template_decorator import get_template_manager
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.templates_manager import TemplateConfig
from aoe2mapgenerator.units.placers.gate_placer import GatePlacer
from aoe2mapgenerator.units.placers.group_placer import GroupPlacer
from aoe2mapgenerator.units.placers.path_placer import PathPlacer
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.placer_configs import (
    AddBordersConfig,
    PlaceGateOnFourSidesConfig,
    PlaceGateOnEightSidesConfig,
    PlaceGroupsConfig,
    PlacePathConfig,
    PointSelectorConfig,
    VisualizeMapConfig,
    VoronoiGeneratorConfig,
)
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
    PointManager,
)
from aoe2mapgenerator.units.placers.wall_placer import WallPlacer
from aoe2mapgenerator.units.wallgenerators.voronoi import VoronoiGenerator
from aoe2mapgenerator.visualizer.visualizer import Visualizer


class MapManager(IMapManager):
    """Facade that owns all map-layer state and delegates to specialist helpers.

    Internal collaborators (placers, generators, visualiser) are created once
    in ``__init__`` and are considered implementation details.  Only ``map``,
    ``output_dir``, and the public methods below form the stable API.

    Args:
        map_size: Side length of the square map in tiles.
        output_dir: Directory where scenario files are written.  Defaults to a
            cross-platform temp directory so the library works out-of-the-box
            on any OS.  Override with your AoE2 scenario folder path.
        seed: Optional integer seed that pins *all* random decisions made
            during map generation.  Two ``MapManager`` instances created with
            the same *seed* produce identical output.  Pass ``None`` (default)
            for a non-deterministic map.
    """

    def __init__(
        self,
        map_size: int,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        seed: int | None = None,
    ) -> None:
        self.map: Map = Map(size=map_size)
        self.output_dir: str = output_dir
        self.seed: int | None = seed
        self.templates: list[str] = []

        # Seeded RNG shared by all collaborators that consume randomness.
        # Pass ``self.rng`` down to any new collaborator that needs randomness.
        self.rng: _random.Random = _random.Random(seed)

        os.makedirs(self.output_dir, exist_ok=True)
        # Scenario is created lazily on first write so that MapManager can be
        # instantiated in environments that don't have the base .aoe2scenario
        # file available (e.g. CI, unit tests, notebooks).
        self.scenario: Scenario | None = None

        # Internal collaborators — treat as private.
        # NOTE: Any object added here *must* also appear in _map_collaborators
        # below so that load_map() rewires it automatically.
        self._base_placer: PlacerBase = PlacerBase(self.map)
        self._wall_placer: WallPlacer = WallPlacer(self.map)
        self._gate_placer: GatePlacer = GatePlacer(self.map)
        self._group_placer: GroupPlacer = GroupPlacer(self.map)
        self._path_placer: PathPlacer = PathPlacer(self.map)
        self._voronoi_generator: VoronoiGenerator = VoronoiGenerator(self.map)
        self._terrain_generator: PerlinTerrainGenerator = PerlinTerrainGenerator(self.map)
        self._point_manager: PointManager = PointManager(self.map)
        self._visualizer: Visualizer = Visualizer(self.map)
        self.template_manager = get_template_manager()

        # Registry of objects whose ``.map`` attribute must be updated by
        # ``load_map()``.  Add new collaborators here — never in load_map().
        self._map_collaborators: list[Any] = [
            self._base_placer,
            self._wall_placer,
            self._gate_placer,
            self._group_placer,
            self._path_placer,
            self._voronoi_generator,
            self._terrain_generator,
            self._point_manager,
            self._visualizer,
        ]

    def load_map(self, map_obj: Map) -> None:
        """Replace the current map and rewire all internal collaborators.

        This is the correct way to restore a previously serialised map into a
        ``MapManager`` so that all placers and helpers operate on the loaded
        data rather than the blank map created in ``__init__``.

        Adding a collaborator?  Append it to ``self._map_collaborators`` in
        ``__init__`` — **not** here.

        Args:
            map_obj: Deserialised :class:`~aoe2mapgenerator.map.map.Map` to
                load.  Must have the same ``size`` as this ``MapManager``.
        """
        self.map = map_obj
        # Rewire every registered collaborator via the registry.
        for collaborator in self._map_collaborators:
            collaborator.map = map_obj
        # Keep scenario writer bound to the active map as well.
        if self.scenario is not None:
            self.scenario.map = map_obj

    # ------------------------------------------------------------------
    # IMapManager protocol properties (read-only access to collaborators)
    # ------------------------------------------------------------------

    @property
    def base_placer(self) -> PlacerBase:
        return self._base_placer

    @property
    def wall_placer(self) -> WallPlacer:
        return self._wall_placer

    @property
    def gate_placer(self) -> GatePlacer:
        return self._gate_placer

    @property
    def group_placer(self) -> GroupPlacer:
        return self._group_placer

    @property
    def voronoi_generator(self) -> VoronoiGenerator:
        return self._voronoi_generator

    @property
    def path_placer(self) -> PathPlacer:
        return self._path_placer

    @property
    def point_manager(self) -> PointManager:
        return self._point_manager

    @property
    def visualizer(self) -> Visualizer:
        return self._visualizer

    # ------------------------------------------------------------------
    # Public map-building API
    # ------------------------------------------------------------------

    def configure_scenario(self, config: ScenarioConfig) -> "MapManager":
        """Apply scenario-level and player-level configuration.

        This must be called **before** :meth:`write_map_and_save` so the
        settings are reflected in the written file.

        Internally this delegates to
        :func:`aoe2mapgenerator.scenario.scenario_config.configure_scenario`.

        Args:
            config: A :class:`ScenarioConfig` describing player names,
                civilizations, starting resources, and diplomacy.

        Returns:
            self, for method chaining.

        Example::

            mm.configure_scenario(
                ScenarioConfig(
                    map_name="Valley of Shadows",
                    players=[
                        PlayerConfig(
                            player_id=PlayerId.ONE,
                            name="House Valen",
                            civilization=36,  # Franks
                            starting_gold=500,
                        ),
                    ],
                    enemy_pairs=[(PlayerId.ONE, PlayerId.TWO)],
                )
            )
        """
        if self.scenario is None:
            self.scenario = Scenario(self.map)
        _configure_scenario(self.scenario.scenario, config)
        return self

    def write_map_and_save(self, file_name: str) -> "MapManager":
        """Write the map to a scenario file and save it to disk.

        Args:
            file_name: File name (without leading path) to write inside
                ``self.output_dir``.

        Returns:
            self, for method chaining.
        """
        if self.scenario is None:
            self.scenario = Scenario(self.map)
        # Ensure scenario serialization writes the current map instance.
        self.scenario.map = self.map
        self.scenario._change_map_size(self.map.size)
        self.scenario.write_map()
        self.scenario.save_file(os.path.join(self.output_dir, file_name))
        return self

    def place_groups(self, configuration: PlaceGroupsConfig) -> "MapManager":
        """Place groups of objects on the map.

        Returns:
            self, for method chaining.
        """
        self._group_placer.place_groups(configuration)
        return self

    def place_borders(self, configuration: AddBordersConfig) -> "MapManager":
        """Add border objects around a region of the map.

        Returns:
            self, for method chaining.
        """
        self._wall_placer.add_borders(configuration)
        return self

    def place_voronoi_zones(
        self, configuration: VoronoiGeneratorConfig
    ) -> List[MapObject]:
        """Generate Voronoi cells and return the resulting MapObjects."""
        return self._voronoi_generator.generate_voronoi_cells(configuration)

    def generate_perlin_terrain(self, config: PerlinTerrainConfig) -> "MapManager":
        """Generate Perlin-based terrain and elevation into the map.

        The supplied config controls both noise sampling and how the normalized
        noise values are quantized into terrain IDs and elevation levels.
        """
        self._terrain_generator.generate_perlin_terrain(config)
        return self

    def visualize_map(self, configuration: VisualizeMapConfig) -> "MapManager":
        """Render a visual representation of the map.

        Returns:
            self, for method chaining.
        """
        self._visualizer.visualize_mat(configuration)
        return self

    def select_points(
        self, configuration: PointSelectorConfig
    ) -> list[tuple[int, int]]:
        """Return points from a map layer matching a filter configuration.

        Note: Does not support method chaining (returns point list, not self).
        """
        return self._point_manager.point_selector.get_points_from_map_layer(configuration)

    def get_map(self) -> Map:
        """Return the underlying Map object."""
        return self.map

    def create_path(self, configuration: "PlacePathConfig") -> "MapManager":
        """Trace and place a randomised path connecting key points.

        Returns:
            self, for method chaining.
        """
        self._path_placer.create_path(configuration)
        return self

    def place_gates_on_four_sides(
        self, configuration: "PlaceGateOnFourSidesConfig"
    ) -> "MapManager":
        """Place gates at the four cardinal-direction extremes of a region.

        Returns:
            self, for method chaining.
        """
        self._gate_placer.place_gate_on_four_sides(
            configuration.point_collection,
            configuration.map_layer_type,
            configuration.gate_type,
            configuration.player_id,
        )
        return self

    def place_gates_on_eight_sides(
        self, configuration: "PlaceGateOnEightSidesConfig"
    ) -> "MapManager":
        """Place gates at all eight compass-direction extremes of a region.

        Returns:
            self, for method chaining.
        """
        self._gate_placer.place_gate_on_eight_sides(
            configuration.point_collection,
            configuration.map_layer_type,
            configuration.gate_type,
            configuration.player_id,
        )
        return self

    def get_map_layer(self, map_layer_type: MapLayerType):
        """Return the MapLayer for the given layer type."""
        return self.map.get_map_layer(map_layer_type)

    def get_dictionary(self, map_layer_type: MapLayerType) -> dict:
        """Return the dict representation of a map layer."""
        return self.map.get_map_layer(map_layer_type).get_dict()

    def get_array(self, map_layer_type: MapLayerType) -> list[list[MapObject]]:
        """Return the 2-D array representation of a map layer."""
        return self.map.get_map_layer(map_layer_type).get_array()

    def get_set_with_map_object(
        self, map_layer_type: MapLayerType, obj: MapObject
    ) -> set[tuple[int, int]]:
        """Return all tile coordinates occupied by a given MapObject."""
        return self.map.get_map_layer(map_layer_type).get_set_with_map_object(obj)

    def get_points_from_map_layer(
        self, configuration: PointSelectorConfig
    ) -> list[tuple[int, int]]:
        """Alias for ``select_points`` — returns filtered points from a layer."""
        return self._point_manager.point_selector.get_points_from_map_layer(configuration)

    def points(self) -> PointManager:
        """Return the PointManager for direct point-collection operations."""
        return self._point_manager

    # ------------------------------------------------------------------
    # Convenience point helpers
    # ------------------------------------------------------------------

    def all_points(self, name: str = "_all_points") -> PointCollection:
        """Return a ``PointCollection`` containing every tile on the map.

        The collection is freshly computed on each call and registered under
        *name*.  Pass a unique name when you need multiple independent copies
        in the same session.

        Args:
            name: Registry name for the new collection.  Must not already exist
                unless the previous one was removed.

        Returns:
            A ``PointCollection`` pre-populated with all ``(x, y)`` tiles.
        """
        size = self.map.size
        return self._point_manager.add_point_collection(
            name,
            [(x, y) for x in range(size) for y in range(size)],
            make_unique=True,
        )

    def points_in_rect(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        name: str = "_rect",
    ) -> PointCollection:
        """Return a ``PointCollection`` for the axis-aligned rectangle ``(x1,y1)→(x2,y2)``.

        Coordinates are clamped to map bounds, so over-extending the rectangle
        is safe.

        Args:
            x1: Left column (inclusive).
            y1: Top row (inclusive).
            x2: Right column (inclusive).
            y2: Bottom row (inclusive).
            name: Registry name for the new collection.

        Returns:
            PointCollection for the specified rectangle.
        """
        size = self.map.size
        xs = range(max(0, min(x1, x2)), min(size, max(x1, x2) + 1))
        ys = range(max(0, min(y1, y2)), min(size, max(y1, y2) + 1))
        return self._point_manager.add_point_collection(
            name,
            [(x, y) for x in xs for y in ys],
            make_unique=True,
        )

    def points_from_zone(
        self,
        zone_obj: MapObject,
        name: str = "_zone",
    ) -> PointCollection:
        """Return a ``PointCollection`` of every tile occupied by *zone_obj* in the ZONE layer.

        This is the canonical way to retrieve all tiles belonging to one
        Voronoi zone after calling ``place_voronoi_zones()``.

        Args:
            zone_obj: The ``MapObject`` representing the zone.
            name: Registry name for the new collection.

        Returns:
            PointCollection containing the zone's tiles.
        """
        tiles = self.map.get_map_layer(MapLayerType.ZONE).get_array_of_points(zone_obj)
        return self._point_manager.add_point_collection(
            name,
            list(tiles),
            make_unique=True,
        )

    # ------------------------------------------------------------------
    # Template helpers
    # ------------------------------------------------------------------

    def apply_template(
        self,
        point_collection: PointCollection,
        template_type: TemplateType,
        config: TemplateConfig,
        **kwargs: Any,
    ) -> "MapManager":
        """Apply a registered template to the map.

        Args:
            point_collection: The set of candidate tile positions.
            template_type: Which template to apply.
            config: Template-specific configuration.
            **kwargs: Extra keyword arguments forwarded to the template.

        Returns:
            self, for method chaining.
        """
        self.template_manager.apply_template(self, point_collection, template_type, config, **kwargs)
        return self

    def create_fort(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] = (50, 50),
        size: int = 20,
        player_id: PlayerId = PlayerId.ONE,
        gate_type: GateType = GateType.FORTIFIED_GATE,
        **kwargs: Any,
    ) -> "MapManager":
        """Place a fort (walls + gates) on the map.

        Args:
            point_collection: Candidate tile positions.
            center_point: Centre coordinates of the fort.
            size: Half-width of the fort square.
            player_id: Player who owns the fort.
            gate_type: Gate style to use.
            **kwargs: Extra keyword arguments forwarded to the template.

        Returns:
            self, for method chaining.
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=center_point,
            size=size,
            player_id=player_id,
            gate_type=gate_type,
        )
        return self.apply_template(point_collection, TemplateType.FORT, config=config, **kwargs)

    def create_city(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] = (120, 120),
        size: int | None = None,
        player_id: PlayerId = PlayerId.ONE,
        gate_type: GateType = GateType.CITY_GATE,
        preset: str = "balanced",
        **kwargs: Any,
    ) -> "MapManager":
        """Place a full city template (districts + walls + gates + roads).

        Args:
            point_collection: Candidate tile positions.
            center_point: Centre coordinates of the city.
            size: City radius. If omitted, the selected ``preset`` determines radius.
            player_id: Player who owns the city.
            gate_type: Gate style to use for city walls.
            preset: One of ``compact``, ``balanced``, ``mega_city`` (or ``mega`` alias).
            **kwargs: Extra keyword arguments forwarded to CityTemplate.

        Returns:
            self, for method chaining.
        """
        resolved_size = size if size is not None else 0
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=center_point,
            size=resolved_size,
            player_id=player_id,
            gate_type=gate_type,
        )
        kwargs.setdefault("preset", preset)
        if size is not None:
            kwargs.setdefault("city_radius", size)
        return self.apply_template(point_collection, TemplateType.CITY, config=config, **kwargs)

    def create_palace(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] = (120, 120),
        size: int = 22,
        player_id: PlayerId = PlayerId.ONE,
        gate_type: GateType = GateType.FORTIFIED_GATE,
        **kwargs: Any,
    ) -> "MapManager":
        """Place a fortified palace complex with moat, gardens, and elite guard."""
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=center_point,
            size=size,
            player_id=player_id,
            gate_type=gate_type,
        )
        kwargs.setdefault("radius", size)
        return self.apply_template(point_collection, TemplateType.PALACE, config=config, **kwargs)

    def create_oak_forest(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.01,
        group_size: int = 12,
        clumping: int = 5,
        **kwargs: Any,
    ) -> PointCollection:
        """Scatter an oak forest across the given point collection.

        Args:
            point_collection: Candidate tile positions for tree placement.
            groups_density: Fraction of available points used as group seeds.
            group_size: Number of trees per group.
            clumping: Spread factor (0 = tightly clumped, higher = spread).
            **kwargs: Extra keyword arguments forwarded to OakForestTemplate.

        Returns:
            PointCollection of tiles that were actually populated.
        """
        return OakForestTemplate.generate(
            self,
            point_collection,
            player_id=PlayerId.GAIA,
            groups_density=groups_density,
            group_size=group_size,
            clumping=clumping,
            **kwargs,
        )

    def create_snow_forest(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.012,
        group_size: int = 10,
        clumping: int = 5,
        **kwargs: Any,
    ) -> PointCollection:
        """Scatter a snow forest (snow terrain + snow pine trees + arctic fauna).

        Args:
            point_collection: Candidate tile positions.
            groups_density: Fraction of points used as tree-group seeds.
            group_size: Number of trees per group.
            clumping: Tree cluster tightness.
            **kwargs: Extra keyword arguments forwarded to SnowForestTemplate.
        """
        return SnowForestTemplate.generate(
            self,
            point_collection,
            player_id=PlayerId.GAIA,
            groups_density=groups_density,
            group_size=group_size,
            clumping=clumping,
            **kwargs,
        )

    def _create_nature_template(
        self,
        point_collection: PointCollection,
        template_type: TemplateType,
        groups_density: float,
        group_size: int,
        clumping: int,
        center_point: Tuple[int, int] | None = None,
        size: int = 10,
        **kwargs: Any,
    ) -> PointCollection:
        """Internal helper: apply a nature template via the registered template manager."""
        if len(point_collection.get_point_list()) == 0:
            return point_collection
        effective_center = center_point or point_collection.get_average_point_position()
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=effective_center,
            size=size,
            player_id=PlayerId.GAIA,
        )
        self.apply_template(
            point_collection,
            template_type,
            config=config,
            groups_density=groups_density,
            group_size=group_size,
            clumping=clumping,
            center_point=effective_center,
            size=size,
            **kwargs,
        )
        return point_collection

    def create_pond(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] | None = None,
        size: int = 8,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a freshwater pond (shallows terrain + fish + reeds).

        Args:
            point_collection: Candidate tile positions.
            center_point: Centre of the pond; defaults to centroid of selection.
            size: Pond radius in tiles.  Default 8.
            **kwargs: Forwarded to PondTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.POND,
            groups_density=0.0, group_size=0, clumping=0,
            center_point=center_point, size=size, **kwargs,
        )

    def create_river_segment(
        self,
        point_collection: PointCollection,
        **kwargs: Any,
    ) -> PointCollection:
        """Fill the selected region with a river (shallow water terrain + fish).

        The caller selects the river channel.  This method fills it with
        WATER_SHALLOW terrain and populates it with fish and shore reeds.

        Args:
            point_collection: Tiles forming the river channel.
            **kwargs: Forwarded to RiverSegmentTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.RIVER_SEGMENT,
            groups_density=0.0, group_size=0, clumping=0, **kwargs,
        )

    def create_pine_forest(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.01,
        group_size: int = 12,
        clumping: int = 5,
        **kwargs: Any,
    ) -> PointCollection:
        """Scatter a pine forest (trees + deer + wolves + rocks).

        Args:
            point_collection: Candidate tile positions.
            groups_density: Fraction of points used as tree-group seeds.
            group_size: Number of trees per group.
            clumping: Tree cluster tightness.
            **kwargs: Extra keyword arguments forwarded to PineForestTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.PINE_FOREST,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            **kwargs,
        )

    def create_winter_landscape(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.01,
        group_size: int = 10,
        clumping: int = 5,
        center_point: Tuple[int, int] | None = None,
        size: int = 6,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a winter biome (snow terrain + frozen pond + arctic fauna).

        Args:
            point_collection: Candidate tile positions.
            groups_density: Tree density.
            group_size: Trees per group.
            clumping: Tree cluster tightness.
            center_point: Centre for the frozen pond; defaults to centroid.
            size: Radius of the frozen pond in tiles.  Default 6.
            **kwargs: Forwarded to WinterLandscapeTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.WINTER_LANDSCAPE,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            center_point=center_point, size=size, **kwargs,
        )

    def create_desert(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.005,
        group_size: int = 6,
        clumping: int = 4,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a desert biome (sand terrain + palms + cacti + desert fauna).

        Args:
            point_collection: Candidate tile positions.
            groups_density: Vegetation density.
            group_size: Objects per group.
            clumping: Cluster tightness.
            **kwargs: Forwarded to DesertTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.DESERT,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            **kwargs,
        )

    def create_desert_oasis(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.004,
        group_size: int = 5,
        clumping: int = 4,
        center_point: Tuple[int, int] | None = None,
        size: int = 10,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a desert biome with a central freshwater oasis.

        Args:
            point_collection: Candidate tile positions.
            groups_density: Background vegetation density.
            group_size: Objects per group.
            clumping: Cluster tightness.
            center_point: Centre of the oasis pool; defaults to centroid.
            size: Oasis pool radius in tiles.  Default 10.
            **kwargs: Forwarded to DesertOasisTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.DESERT_OASIS,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            center_point=center_point, size=size, **kwargs,
        )

    def create_savannah(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.003,
        group_size: int = 4,
        clumping: int = 3,
        **kwargs: Any,
    ) -> PointCollection:
        """Create an African savannah biome.

        Args:
            point_collection: Candidate tile positions.
            groups_density: Tree density (savannahs are open — keep low).
            group_size: Trees per group.
            clumping: Cluster tightness.
            **kwargs: Forwarded to SavannahTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.SAVANNAH,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            **kwargs,
        )

    def create_rainforest(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.015,
        group_size: int = 14,
        clumping: int = 6,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a dense tropical rainforest biome.

        Args:
            point_collection: Candidate tile positions.
            groups_density: Tree density (dense — keep high).
            group_size: Trees per group.
            clumping: Cluster tightness.
            **kwargs: Forwarded to RainforestTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.RAINFOREST,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            **kwargs,
        )

    def create_mediterranean(
        self,
        point_collection: PointCollection,
        groups_density: float = 0.008,
        group_size: int = 8,
        clumping: int = 4,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a Mediterranean woodland biome.

        Args:
            point_collection: Candidate tile positions.
            groups_density: Tree density.
            group_size: Trees per group.
            clumping: Cluster tightness.
            **kwargs: Forwarded to MediterraneanTemplate.
        """
        return self._create_nature_template(
            point_collection, TemplateType.MEDITERRANEAN,
            groups_density=groups_density, group_size=group_size, clumping=clumping,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Convenience wrappers for the map-content toolkit templates
    # ------------------------------------------------------------------

    def create_fauna_scatter(
        self,
        point_collection: PointCollection,
        herd_count: int = 6,
        predator_count: int = 3,
        herd_size: Tuple[int, int] = (3, 6),
        **kwargs: Any,
    ) -> PointCollection:
        """Scatter wild animal herds and lone predators across a region.

        Args:
            point_collection: Candidate tile positions.
            herd_count: Number of herd clusters.
            predator_count: Number of lone predators.
            herd_size: Inclusive (min, max) members per herd.
            **kwargs: Forwarded to FaunaScatterTemplate.
        """
        return self._apply_content_template(
            point_collection, TemplateType.FAUNA_SCATTER,
            herd_count=herd_count, predator_count=predator_count,
            herd_size=herd_size, **kwargs,
        )

    def create_berry_bush(
        self,
        point_collection: PointCollection,
        density: float = 0.02,
        **kwargs: Any,
    ) -> PointCollection:
        """Scatter forage / fruit bushes (a berry patch) across a region.

        Args:
            point_collection: Candidate tile positions.
            density: Approximate fraction of tiles that receive a bush.
            **kwargs: Forwarded to BerryBushTemplate.
        """
        return self._apply_content_template(
            point_collection, TemplateType.BERRY_BUSH, density=density, **kwargs,
        )

    def create_bandit_camp(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] | None = None,
        size: int = 10,
        tents: int = 5,
        bandits: int = 6,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a small hostile bandit camp (dirt patch, bonfire, tents, bandits).

        Args:
            point_collection: Candidate tile positions.
            center_point: Camp centre; defaults to the region centroid.
            size: Camp radius in tiles.
            tents: Number of tents in the ring.
            bandits: Number of bandit units.
            **kwargs: Forwarded to BanditCampTemplate.
        """
        return self._apply_content_template(
            point_collection, TemplateType.BANDIT_CAMP,
            center_point=center_point, size=size, tents=tents, bandits=bandits,
            **kwargs,
        )

    def create_snowy_mountain_range(
        self,
        point_collection: PointCollection,
        max_elevation: int = 6,
        **kwargs: Any,
    ) -> PointCollection:
        """Create an elongated snow-mountain ridgeline with elevation.

        Args:
            point_collection: Candidate tile positions (elongated for best shape).
            max_elevation: Peak elevation at the ridge (0–7).
            **kwargs: Forwarded to SnowyMountainRangeTemplate.
        """
        return self._apply_content_template(
            point_collection, TemplateType.SNOWY_MOUNTAIN_RANGE,
            max_elevation=max_elevation, **kwargs,
        )

    def create_lush_forest(
        self,
        point_collection: PointCollection,
        tree_density: float = 0.15,
        clearings: int = 3,
        **kwargs: Any,
    ) -> PointCollection:
        """Create a dense mixed forest with berry bushes, fauna, and clearings.

        Args:
            point_collection: Candidate tile positions.
            tree_density: Approximate fraction of tiles that receive a tree.
            clearings: Number of open clearings.
            **kwargs: Forwarded to LushForestTemplate.
        """
        return self._apply_content_template(
            point_collection, TemplateType.LUSH_FOREST,
            tree_density=tree_density, clearings=clearings, **kwargs,
        )

    def _apply_content_template(
        self,
        point_collection: PointCollection,
        template_type: TemplateType,
        **kwargs: Any,
    ) -> PointCollection:
        """Internal helper: apply a content-toolkit template via the manager."""
        if len(point_collection.get_point_list()) == 0:
            return point_collection
        effective_center = kwargs.get(
            "center_point", point_collection.get_average_point_position()
        )
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=effective_center,
            player_id=PlayerId.GAIA,
        )
        self.apply_template(point_collection, template_type, config=config, **kwargs)
        return point_collection

    # ------------------------------------------------------------------
    # Convenience wrappers for the new structural templates
    # ------------------------------------------------------------------

    def create_walls(
        self,
        point_collection: PointCollection,
        gate_type: GateType = GateType.FORTIFIED_GATE,
        border_width: int = 1,
        player_id: PlayerId = PlayerId.ONE,
        **kwargs: Any,
    ) -> "MapManager":
        """Place a perimeter wall around a region.

        Args:
            point_collection: Tiles forming the region to wall off.
            gate_type: Wall material / gate style.
            border_width: Wall thickness in tiles.
            player_id: Player who owns the walls.
            **kwargs: Forwarded to WallsTemplate.

        Returns:
            self, for method chaining.
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=point_collection.get_average_point_position(),
            player_id=player_id,
            gate_type=gate_type,
        )
        self.apply_template(
            point_collection,
            TemplateType.WALLS,
            config=config,
            gate_type=gate_type,
            border_width=border_width,
            player_id=player_id,
            **kwargs,
        )
        return self

    def create_road(
        self,
        point_collection: PointCollection,
        key_points: List[Tuple[int, int]] | None = None,
        width: int = 1,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs: Any,
    ) -> "MapManager":
        """Trace a dirt road through a region.

        Args:
            point_collection: Valid tile canvas for the road.
            key_points: Ordered ``(x, y)`` waypoints.  If ``None`` the road
                runs left-to-right across the bounding box midline.
            width: Road width in tiles.
            player_id: Owner of terrain objects.
            **kwargs: Forwarded to RoadTemplate.

        Returns:
            self, for method chaining.
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=point_collection.get_average_point_position(),
            player_id=player_id,
        )
        kw: dict[str, Any] = {"key_points": key_points or [], "width": width, "player_id": player_id}
        kw.update(kwargs)
        self.apply_template(point_collection, TemplateType.ROAD, config=config, **kw)
        return self

    def create_mine(
        self,
        point_collection: PointCollection,
        resource: str = "GOLD",
        num_piles: int = 4,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs: Any,
    ) -> "MapManager":
        """Place a resource mine cluster.

        Args:
            point_collection: Region for the mine.
            resource: ``"GOLD"`` or ``"STONE"``.
            num_piles: Number of resource pile groups.
            player_id: Owner (GAIA for neutral mines).
            **kwargs: Forwarded to MineTemplate.

        Returns:
            self, for method chaining.
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=point_collection.get_average_point_position(),
            player_id=player_id,
        )
        self.apply_template(
            point_collection,
            TemplateType.MINE,
            config=config,
            resource=resource,
            num_piles=num_piles,
            player_id=player_id,
            **kwargs,
        )
        return self

    def create_mountain(
        self,
        point_collection: PointCollection,
        max_elevation: int = 4,
        player_id: PlayerId = PlayerId.GAIA,
        **kwargs: Any,
    ) -> "MapManager":
        """Create a rocky elevated terrain feature.

        Args:
            point_collection: Tiles forming the mountain area.
            max_elevation: Peak elevation at centre (0–7).
            player_id: Owner of terrain objects.
            **kwargs: Forwarded to MountainTemplate.

        Returns:
            self, for method chaining.
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=point_collection.get_average_point_position(),
            player_id=player_id,
        )
        self.apply_template(
            point_collection,
            TemplateType.MOUNTAIN,
            config=config,
            max_elevation=max_elevation,
            player_id=player_id,
            **kwargs,
        )
        return self

    def create_castle(
        self,
        point_collection: PointCollection,
        center_point: Tuple[int, int] | None = None,
        player_id: PlayerId = PlayerId.ONE,
        gate_type: GateType = GateType.STONE_GATE,
        **kwargs: Any,
    ) -> "MapManager":
        """Place a fortified castle complex.

        Delegates to ``FortTemplate`` for the walls/gates then places a Castle
        building at the centre with elite guard units.

        Args:
            point_collection: Candidate tile positions.
            center_point: Castle centre tile.  Defaults to the centroid.
            player_id: Owning player.
            gate_type: Gate / wall style.
            **kwargs: Forwarded to CastleTemplate.

        Returns:
            self, for method chaining.
        """
        effective_center = center_point or point_collection.get_average_point_position()
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=effective_center,
            player_id=player_id,
            gate_type=gate_type,
        )
        self.apply_template(
            point_collection,
            TemplateType.CASTLE,
            config=config,
            center_point=effective_center,
            player_id=player_id,
            gate_type=gate_type,
            **kwargs,
        )
        return self

    def create_river(
        self,
        point_collection: PointCollection,
        from_point: Tuple[int, int] | None = None,
        to_point: Tuple[int, int] | None = None,
        width: int = 3,
        **kwargs: Any,
    ) -> "MapManager":
        """Trace an edge-to-edge river across a region.

        Args:
            point_collection: Tiles available for the river channel.
            from_point: River entry tile.  Defaults to left-centre of bbox.
            to_point: River exit tile.  Defaults to right-centre of bbox.
            width: River width in tiles.
            **kwargs: Forwarded to RiverTemplate.

        Returns:
            self, for method chaining.
        """
        config = TemplateConfig(
            point_collection=point_collection,
            center_point=point_collection.get_average_point_position(),
            player_id=PlayerId.GAIA,
        )
        kw: dict[str, Any] = {"width": width}
        if from_point is not None:
            kw["from_point"] = from_point
        if to_point is not None:
            kw["to_point"] = to_point
        kw.update(kwargs)
        self.apply_template(point_collection, TemplateType.RIVER, config=config, **kw)
        return self
