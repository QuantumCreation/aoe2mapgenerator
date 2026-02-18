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

from aoe2mapgenerator.common.constants.constants import (
    BASE_SCENARIO_NAME,
    BASE_SCENE_DIR_WINDOWS_WSL,
    DEFAULT_PLAYER,
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.common.types import AOE2ObjectType, Point
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.scenario.scenario import Scenario
from aoe2mapgenerator.templates.decor import OakForestTemplate
from aoe2mapgenerator.templates.template_decorator import get_template_manager
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.templates_manager import TemplateConfig
from aoe2mapgenerator.units.placers.gate_placer import GatePlacer
from aoe2mapgenerator.units.placers.group_placer import GroupPlacer
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.placer_configs import (
    AddBordersConfig,
    PlaceGroupsConfig,
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
    """

    def __init__(self, map_size: int, output_dir: str = BASE_SCENE_DIR_WINDOWS_WSL) -> None:
        self.map: Map = Map(size=map_size)
        self.output_dir: str = output_dir
        self.templates: list[str] = []

        self.scenario: Scenario = Scenario(
            self.map, os.path.join(self.output_dir, BASE_SCENARIO_NAME)
        )

        # Internal collaborators — treat as private
        self._base_placer: PlacerBase = PlacerBase(self.map)
        self._wall_placer: WallPlacer = WallPlacer(self.map)
        self._gate_placer: GatePlacer = GatePlacer(self.map)
        self._group_placer: GroupPlacer = GroupPlacer(self.map)
        self._voronoi_generator: VoronoiGenerator = VoronoiGenerator(self.map)
        self._point_manager: PointManager = PointManager(self.map)
        self._visualizer: Visualizer = Visualizer(self.map)
        self.template_manager = get_template_manager()

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
    def point_manager(self) -> PointManager:
        return self._point_manager

    @property
    def visualizer(self) -> Visualizer:
        return self._visualizer

    # ------------------------------------------------------------------
    # Public map-building API
    # ------------------------------------------------------------------

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