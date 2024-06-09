"""
Configuration for the methods for various placers
"""

from dataclasses import dataclass


from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import (
    MapLayerType,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType


from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import DEFAULT_PLAYER
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from typing import Callable
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.utils import default_clumping_func


@dataclass
class AddBordersConfig:
    """
    Configuration for adding borders to a map.

    Args:
        point_manager (PointManager): Manages the points to be placed.
        map_layer_type (MapLayerType): The map type.
        obj_type (AOE2ObjectType): The type of object to be placed.
        player_id (PlayerId = DEFAULT_PLAYER): Id of the objects being placed.
        margin (int = 1): Margin between each object and any other object.
    """

    point_manager: PointManager
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    player_id: PlayerId = DEFAULT_PLAYER
    margin: int = 1


@dataclass
class PlaceGroupsConfig:
    """
    Configuration for placing groups of objects on a map.

    Args:
        point_manager (PointManager): Manages the points to be placed.
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

    point_manager: PointManager
    map_layer_type: MapLayerType
    obj_type: AOE2ObjectType
    player_id: PlayerId = DEFAULT_PLAYER
    groups: int = 1
    group_size: int = 1
    group_density: int | None = None
    groups_density: int | None = None
    clumping: int = 0
    clumping_func: Callable = default_clumping_func
    margin: int = 0
    start_point: tuple | None = None


@dataclass
class VoronoiGeneratorConfig:
    """
    Configuration for generating Voronoi diagrams.

    Args:
        point_manager (PointManager): Manages the points to be placed.
        map_layer_type (MapLayerType): The map type.
        obj_type (AOE2ObjectType): The type of object to be placed.
    """

    point_manager: PointManager
    interpoint_distance: int
    map_layer_type: MapLayerType


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
    """

    map_layer_type: MapLayerType
    include_zones: bool = False
    transpose: bool = False
    fig_size: tuple[int, int] = (5, 5)
    include_legend: bool = False


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
