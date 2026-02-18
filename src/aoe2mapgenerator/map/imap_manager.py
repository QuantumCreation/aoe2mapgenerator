"""IMapManager \u2014 structural Protocol for MapManager.

Defines the stable public contract that any MapManager implementation must
satisfy.  Code that only needs to *use* a MapManager (e.g. templates,
services) should type-hint against ``IMapManager`` rather than the concrete
class, making both testing and alternative implementations straightforward.

Design notes
------------
* Mutable attributes (``map``, ``output_dir``, ``templates``, ``scenario``)
  are part of the public API and appear as simple attribute annotations.
* Internal collaborators (placers, generators, visualiser) are exposed as
  read-only properties so call-sites can reach them when needed, but callers
  are not expected to replace them.
* All map-mutating methods return ``self`` (typed via TypeVar ``T``) to
  support method chaining.
"""

from typing import Any, Dict, List, Protocol, Set, Tuple, TypeVar

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.scenario.scenario import Scenario
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
from aoe2mapgenerator.units.placers.point_management.point_manager import PointManager
from aoe2mapgenerator.units.placers.wall_placer import WallPlacer
from aoe2mapgenerator.units.wallgenerators.voronoi import VoronoiGenerator
from aoe2mapgenerator.visualizer.visualizer import Visualizer

T = TypeVar("T", bound="IMapManager")


class IMapManager(Protocol):
    """Structural Protocol describing the MapManager public API.

    Implementors must expose the attributes and methods declared here.
    Use ``isinstance(obj, IMapManager)`` with ``runtime_checkable`` if
    needed \u2014 otherwise rely on static type checking only.
    """

    # ------------------------------------------------------------------
    # Mutable public attributes
    # ------------------------------------------------------------------
    map: Map
    output_dir: str
    templates: list
    scenario: Scenario

    # ------------------------------------------------------------------
    # Read-only collaborator properties
    # ------------------------------------------------------------------

    @property
    def base_placer(self) -> PlacerBase: ...

    @property
    def gate_placer(self) -> GatePlacer: ...

    @property
    def group_placer(self) -> GroupPlacer: ...

    @property
    def point_manager(self) -> PointManager: ...

    @property
    def visualizer(self) -> Visualizer: ...

    @property
    def voronoi_generator(self) -> VoronoiGenerator: ...

    @property
    def wall_placer(self) -> WallPlacer: ...

    # ------------------------------------------------------------------
    # Map-building methods
    # ------------------------------------------------------------------

    def write_map_and_save(self: T, file_name: str) -> T: ...

    def place_groups(self: T, configuration: PlaceGroupsConfig) -> T: ...

    def place_borders(self: T, configuration: AddBordersConfig) -> T: ...

    def place_voronoi_zones(
        self: T, configuration: VoronoiGeneratorConfig
    ) -> List[MapObject]: ...

    def visualize_map(self: T, configuration: VisualizeMapConfig) -> T: ...

    def select_points(
        self: T, configuration: PointSelectorConfig
    ) -> List[Tuple[int, int]]: ...

    def get_map(self: T) -> Map: ...

    def get_map_layer(self: T, map_layer_type: MapLayerType) -> Any: ...

    def get_dictionary(self: T, map_layer_type: MapLayerType) -> Dict: ...

    def get_array(self: T, map_layer_type: MapLayerType) -> List: ...

    def get_set_with_map_object(
        self: T, map_layer_type: MapLayerType, obj: MapObject
    ) -> Set: ...

    def get_points_from_map_layer(
        self: T, configuration: PointSelectorConfig
    ) -> List[Tuple[int, int]]: ...

    def points(self: T) -> PointManager: ...
