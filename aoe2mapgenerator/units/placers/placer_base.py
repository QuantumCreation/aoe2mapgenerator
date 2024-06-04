
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
from aoe2mapgenerator.units.placers.object_info import ObjectInfo
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType

class PlacerBase():

    points_removed_from_point_manager = 0
    points_set_on_map = 0

    def __init__(self, map: Map):
        self.map = map

    def _check_placement(  
        self,
        point_manager: PointManager,
        goal_placement_point: tuple,
        obj_type: AOE2ObjectType = None, 
        margin: int = 0
        ):
        """
        Checks if the given point is a valid placement for an object.

        Args:
            map_layer_type (MapLayerType): The map type.
            point_manager (PointManager): The point manager.
            goal_placement_point (tuple): The point to place the object.
            obj_type (object, optional): The type of object to be placed. Defaults to None.
            margin (int, optional): The margin around the object. Defaults to 0.
            width (int, optional): The width of the object. Defaults to -1.
            height (int, optional): The height of the object. Defaults to -1.
        """

        eff_width = ObjectInfo.get_object_effective_size(obj_type, margin)
        eff_height = ObjectInfo.get_object_effective_size(obj_type, margin)
        
        x, y = goal_placement_point

        for i in range(-margin, eff_width):
            for j in range(-margin, eff_height):
                if not point_manager.check_point_exists((x+i,y+j)):
                    return CheckPlacementReturnTypes.FAIL
        
        return CheckPlacementReturnTypes.SUCCESS

    def _place(
        self, 
        point_manager: PointManager,
        map_layer_type: MapLayerType, 
        point: tuple, 
        obj_type: AOE2ObjectType, 
        player_id: PlayerId, 
        margin: int, 
        ghost_margin: bool
        ):
        """
        Places a single object. Assumes placement has already been verified.

        Args:
            map_layer_type_list: The map type.
            point: Point to place base of object.
            obj_type: The type of object to be placed.
            player_id: Id of the player for the given object.
            margin: Area around the object to be placed.
            ghost_margin: Option to include ghost margins, ie. change neighboring squares so nothing can use them.
            height: Height of a given object.
            width: Width of a given object.
        """

        width = ObjectInfo.get_object_width(obj_type)
        height = ObjectInfo.get_object_height(obj_type)
        eff_width = ObjectInfo.get_object_effective_size(obj_type, margin)
        eff_height = ObjectInfo.get_object_effective_size(obj_type, margin)
        
        x, y = point

        # IDK but this if statement may speed things up a little bit. NEEDS TESTING.
        if ghost_margin or width > 1 or height > 1 or margin > 0:
            for i in range(-margin, eff_width):
                for j in range(-margin, eff_height):

                    if 0<=i<width and 0<=j<height:
                        self.map.set_point(x+i,y+j,GHOST_OBJECT_DISPLACEMENT, map_layer_type, player_id)
                        PlacerBase.points_set_on_map += 1
                        point_manager.remove_point((x+i,y+j))
                        PlacerBase.points_removed_from_point_manager += 1
                    elif ghost_margin:
                        self.map.set_point(x+i,y+j,GHOST_OBJECT_MARGIN, map_layer_type, player_id)
                        PlacerBase.points_set_on_map += 1
                        point_manager.remove_point((x+i,y+j))
                        PlacerBase.points_removed_from_point_manager += 1
        
        self.map.set_point(x+width//2, y+height//2, obj_type, map_layer_type, player_id)
        PlacerBase.points_set_on_map += 1
        point_manager.remove_point((x+width//2, y+height//2))
        PlacerBase.points_removed_from_point_manager += 1

        return

    # ---------------------------- SORTING FUNCTIONS ----------------------------

    def _default_clumping_func(self, p1, p2, clumping):
            """
            Default clumping function.

            Args:
                p1: First point.
                p2: Second point.
                clumping: Factor to determine how clumped placed objects in a group are.
            """
            if clumping == -1:
                clumping = 999
            
            distance = (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
            return (distance)+random.random()*(clumping)**2
