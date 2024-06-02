

import random
from re import A
from site import abs_paths
from telnetlib import GA
from typing import Union, Callable

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
import functools

from aoe2mapgenerator.common.enums.enum import ObjectSize, Directions, MapLayerType, GateTypes, CheckPlacementReturnTypes
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import DEFAULT_OBJECT_TYPES, DEFAULT_PLAYER
from aoe2mapgenerator.common.constants.default_objects import GHOST_OBJECT_DISPLACEMENT, GHOST_OBJECT_MARGIN
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.placer_base import PlacerBase


class WallPlacer(PlacerBase):

    def __init__(self, map: Map):
        super().__init__(map)
    
    # Multiple map type Callableality still seems a bit weird to me. May refactor later.
    def add_borders(
        self, 
        points_manager: PointManager,
        map_layer_type: MapLayerType, 
        obj_type_list: list,
        margin: int = 1, 
        player_id: PlayerId = DEFAULT_PLAYER,
        place_on_n_maps: int = 1,
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            obj_type_list: The type of object to be placed.
            margin: Type of margin to place.
            player_id: Id of the objects being placed.
            place_on_n_maps: Number of maps to place the objects on.
        """
        if player_id is None:
            player_id = DEFAULT_PLAYER
        
        if type(obj_type_list) == list:
            if len(obj_type_list) == 0:
                raise ValueError("Object type list \'{obj_type_list}\' has no entries.")
            obj = obj_type_list[0]
        
        obj = obj_type_list

        # Checks the value types are valid and converts to a list if needed.
        if type(map_layer_type) != list:
            map_layer_type = [map_layer_type]

        if len(map_layer_type) == 0:
            raise ValueError("No elements in value type list.")

        if type(array_space_type_list) != list:
            array_space_type_list = [array_space_type_list]

        points = points_manager.get_point_list()
 
        # Uses only the first value type and array space to find where to place points. May change later.
        # Still places the points in every space.

        for point in points:
            if self._is_on_border(points, point, margin):
                for map_layer_type in map_layer_type[:place_on_n_maps]:
                    x, y = point
                    self.map.set_point(x,y,obj, map_layer_type, player_id)
        
        return
    
    # SOMETHING SOMETIMES LEADS TO MASSIVE PERFORMANCE PROBLEMS HERE. IDK WHY LOL.
    def add_borders_all(
        self, 
        points_manager: PointManager,
        map_layer_type: MapLayerType,
        border_type, 
        margin: int = 1, 
        player_id: PlayerId = DEFAULT_PLAYER,
        place_on_n_maps: int = 1,
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            map_layer_type: The map type.
            border_type: Type of border to place.
            margin: Type of margin to place.
            player_id: Id of the objects being placed.
        """
        
        self.add_borders(
                points_manager, 
                map_layer_type, 
                border_type, 
                margin, 
                player_id=player_id, 
                place_on_n_maps=place_on_n_maps
                )

        return
    
    def _is_on_border(self, points, point, margin):
        """
        Checks if given point is on a border.

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
            margin: Number of squares to fill in along the edge.
        """
        x, y = point

        for i in range(-margin, margin+1):
            for j in range(-abs(abs(i)-margin), abs(abs(i)-margin)+1):
                if not (x+i,y+j) in points:
                    return True

        return False
