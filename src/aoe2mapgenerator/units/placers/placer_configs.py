"""
Configuration for the methods for various placers
"""

from dataclasses import dataclass
from typing import Callable

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    DEFAULT_PLAYER,
    GHOST_OBJECT_DISPLACEMENT_ID,
    LINUX_PROJECT_PATH,
)
from aoe2mapgenerator.common.enums.enum import (
    CheckPlacementReturnTypes,
    GateType,
    MapLayerType,
)
from aoe2mapgenerator.common.types import AOE2ObjectType, Point
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection
from aoe2mapgenerator.units.utils import default_clumping_func


@dataclass
class AddBordersConfig:
    """Configuration for adding border objects around a region.

    Args:
        point_collection: Tiles forming the region interior.
        map_layer_type: Layer on which borders are placed.
        obj_type: Object used to mark each border tile.
        player_id: Owner of the border objects.
        border_width: Perimeter thickness in tiles (>= 1).
    """

    point_collection: PointCollection
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    player_id: PlayerId = DEFAULT_PLAYER
    border_width: int = 1

    def __post_init__(self) -> None:
        if self.border_width < 1:
            raise ValueError(
                f"AddBordersConfig.border_width must be >= 1, got {self.border_width}"
            )


@dataclass
class PlaceGroupsConfig:
    """
    Configuration for placing groups of objects on a map.

    Args:
        point_collection (PointCollection): Manages the points to be placed.
        map_layer_type (MapLayerType): The map type.
        obj_type (AOE2ObjectType): The type of object to be placed.
        player_id (PlayerId = DEFAULT_PLAYER): Id of the objects being placed.
        groups (int = 1): Number of groups to be placed.
        group_size (int = 1): Number of members per group.
        group_density (int = None): Percentage of available points to be used for the group.
        groups_density (int = None): Percentage of available points to be used for the groups.
        clumping (int = 0): How clumped the group members are. 0 is totally clumped. Higher numbers spread members out.
        clumping_func (Callable = None): Function used to calculate the clumping score.
        margin (int = 0): Margin between each object and any other object.
        start_point (tuple = None): The starting point to place the group.
    """

    point_collection: PointCollection
    map_layer_type: MapLayerType
    object_type: AOE2ObjectType
    player_id: PlayerId = DEFAULT_PLAYER
    groups: int = 1
    group_size: int = 1
    group_density: float | None = None
    groups_density: float | None = None
    clumping: int = 0
    clumping_func: Callable = default_clumping_func
    margin: int = 0
    start_point: tuple | None = None

    def __post_init__(self) -> None:
        if self.groups < 1:
            raise ValueError(
                f"PlaceGroupsConfig.groups must be >= 1, got {self.groups}"
            )
        if self.group_size < 1:
            raise ValueError(
                f"PlaceGroupsConfig.group_size must be >= 1, got {self.group_size}"
            )
        if self.margin < 0:
            raise ValueError(
                f"PlaceGroupsConfig.margin must be >= 0, got {self.margin}"
            )
        if self.group_density is not None and not (0.0 <= self.group_density <= 1.0):
            raise ValueError(
                f"PlaceGroupsConfig.group_density must be in [0, 1], got {self.group_density}"
            )
        if self.groups_density is not None and not (0.0 <= self.groups_density <= 1.0):
            raise ValueError(
                f"PlaceGroupsConfig.groups_density must be in [0, 1], got {self.groups_density}"
            )


@dataclass
class VoronoiGeneratorConfig:
    """
    Configuration for generating Voronoi diagrams.

    Args:
        point_manager (PointManager): Manages the points to be placed.
        map_layer_type (MapLayerType): The map type.
        obj_type (AOE2ObjectType): The type of object to be placed.
    """

    point_collection: PointCollection
    interpoint_distance: int
    map_layer_type: MapLayerType

    def __post_init__(self) -> None:
        if self.interpoint_distance <= 0:
            raise ValueError(
                f"VoronoiGeneratorConfig.interpoint_distance must be > 0, "
                f"got {self.interpoint_distance}"
            )


@dataclass
class VisualizeMapConfig:
    """
    Configuration for visualizing the map.

    Args:
        map_layer_type: (MapLayerType): Type of value to visualize.
        include_zones (bool = False): Whether to include zones in the visualization.
        transpose (bool = False): Whether to transpose the map.
        fig_size ((int, int) = (5, 5)): The size of the figure.
        include_legend (bool = False): Whether to include a legend in the visualization.
        anchor ((int, int) = (0, 0)): The anchor point for the legend.
    """

    map_layer_type: MapLayerType
    include_zones: bool = False
    transpose: bool = False
    fig_size: tuple[int, int] = (15, 15)
    include_legend: bool = True
    anchor: tuple[float, float] = (1.25, 1)
    save_figure: bool = False
    file_name: str = "map_visualization.png"
    file_path: str = LINUX_PROJECT_PATH


@dataclass
class PointSelectorConfig:
    """
    Configuration for selecting points on a map.

    Args:
        map_layer_type (MapLayerType): Type of map layer to use.
        object_type (MapObject): Type of object to use.
    """

    map_layer_type: MapLayerType
    object_type: MapObject


@dataclass
class PointSelectorInRangeConfig:
    """
    Configuration for selecting points on a map.

    Args:
        map_layer_type (MapLayerType): Type of map layer to use.
        object_type (MapObject): Type of object to use.
        min_range (int): Minimum range to select points from.
        max_range (int): Maximum range to select points from.
        points_to_be_in_range_of (list[tuple[int, int]]): Points to be in range of.
    """

    map_layer_type: MapLayerType
    object_type: MapObject
    min_range: int
    max_range: int
    points_to_be_in_range_of: list[tuple[int, int]]


@dataclass
class PlaceClosestToPointConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    starting_point: tuple[int, int]
    player_id: PlayerId
    margin: int = 0

@dataclass
class PlaceIfPossibleConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    starting_point: Point
    player_id: PlayerId
    margin: int = 0

@dataclass
class PlaceMultipleConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    points: list[tuple[int, int]]
    obj_type: AOE2ObjectType
    player_id: PlayerId
    margin: int = 0

@dataclass
class FillConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    player_id: PlayerId
    margin: int = 0

@dataclass
class CreateBlockLikeBordersConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    player_id: PlayerId

@dataclass
class PlaceGateOnFourSidesConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    gate_type: GateType
    player_id: PlayerId = DEFAULT_PLAYER

@dataclass
class PlaceGateOnEightSidesConfig:
    point_collection: PointCollection
    map_layer_type: MapLayerType
    gate_type: GateType
    player_id: PlayerId = DEFAULT_PLAYER

@dataclass
class PlacePathConfig:
    """Configuration for path (road) generation.

    Args:
        point_collection: Valid tiles for path placement.
        map_layer_type: Layer on which the path is drawn.
        obj_type: Object used to mark each path tile.
        player_id: Owner of path objects.
        key_points: Ordered waypoints; path visits each in sequence (>= 2).
        num_divisions: Per-segment subdivision counts.
        random_shift_range: Per-segment random offset range in tiles (>= 0 each).
    """

    point_collection: PointCollection
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    player_id: PlayerId
    key_points: list[tuple[int, int]]
    num_divisions: list[int]
    random_shift_range: list[int]

    def __post_init__(self) -> None:
        if len(self.key_points) < 2:
            raise ValueError(
                f"PlacePathConfig.key_points must have at least 2 points, "
                f"got {len(self.key_points)}"
            )
        if len(self.num_divisions) != len(self.random_shift_range):
            raise ValueError(
                "PlacePathConfig.num_divisions and random_shift_range must have "
                f"the same length, got {len(self.num_divisions)} vs "
                f"{len(self.random_shift_range)}"
            )
        for i, s in enumerate(self.random_shift_range):
            if s < 0:
                raise ValueError(
                    f"PlacePathConfig.random_shift_range[{i}] must be >= 0, got {s}"
                )
