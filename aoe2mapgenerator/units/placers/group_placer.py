
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
from aoe2mapgenerator.common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.object_info import ObjectInfo

class GroupPlacerManager(PlacerBase):
    """
    TODO
    """

    points_iterated = 0

    def __init__(self, map: Map):
        super().__init__(map)

    # By default the object is placed in the first value from the map_layer_type list.
    def _place_group(
        self, 
        map_layer_type: MapLayerType, 
        point_manager: PointManager,
        obj_type_list: list = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER,
        group_size: int = 1,
        group_density: int = None,
        clumping: int = 1,
        clumping_func: Callable = None,
        margin: int = 0, 
        start_point: tuple = (-1,-1),
        ghost_margin: bool = True,
        ):
        """
        Places a single group of units on a specific array space.

        Args:
            map_layer_types (list[MapLayerType]): The list of map types.
            array_space_ids (list[Union[int, tuple]]): The list of array space ids to get points for.
            object_types (list, optional): The list of object types to be placed. Defaults to DEFAULT_OBJECT_TYPES.
            player_id (PlayerId, optional): The id of the object to be placed. Defaults to DEFAULT_PLAYER.
            group_size (int, optional): The number of members per group. Defaults to 1.
            group_density (int, optional): The percentage of available points to be used for the group. Defaults to None.
            clumping_factor (int, optional): How clumped the group members are. 0 is totally clumped. Higher numbers spread members out. Defaults to 1.
            clumping_func (Callable, optional): The function used to calculate the clumping score. Defaults to None.
            margin (int, optional): Margin between each object and any other object. Defaults to 0.
            start_point (tuple, optional): The starting point to place the group. Defaults to (-1,-1).
            ghost_margin (bool, optional): Whether to include ghost margins, i.e., change neighboring squares so nothing can use them. Defaults to True.
            place_on_n_maps (int, optional): Places group on the first n maps corresponding to the value types. Defaults to 1.
        """
        if player_id is None:
            player_id = DEFAULT_PLAYER
        
        if clumping_func is None:
            clumping_func = self._default_clumping_func

        points_list = point_manager.get_point_list()
        
        if len(points_list) == 0:
            return
        
        # Adjust group size based on density if specified
        if group_density is not None:
            group_size = group_density*len(points_list)//100

        # Choose a random start point if none is specified or invalid
        if start_point[0] < 0 or start_point[1] < 0:
            start_point = points_list[int(random.random()*len(points_list))]
        else:
            start_point = tuple(start_point)

        total_size = sum(ObjectInfo.get_object_effective_size(obj_type, margin) for obj_type in obj_type_list)
        total_size += (group_size-len(obj_type_list)) * ObjectInfo.get_object_effective_size(obj_type_list[-1], margin) if group_size > len(obj_type_list) else 0

        if clumping == -1:
            random.shuffle(points_list)
        else:
            # Gets points within three times the radius required for the group
            points_list = point_manager.get_nearby_points(start_point, (total_size**(1/2)) * 2) 
            
            # Sort the points based on clumping score if group size is in a certain range
            if 1<group_size<len(points_list):
                points_list = sorted(points_list, key = lambda point: clumping_func(point, start_point, clumping))


        # Try to place objects on the selected points
        obj_counter = 0
        obj_type = obj_type_list[obj_counter]
        placed = 0

        for (x,y) in points_list:
            GroupPlacerManager.points_iterated += 1
            if placed >= group_size:
                return
            
            status = self._check_placement(point_manager, (x,y), obj_type, margin)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return
    
            if status == CheckPlacementReturnTypes.SUCCESS:
                # Place the object on the first n maps
                self._place(point_manager, map_layer_type, (x,y), obj_type, player_id, margin, ghost_margin)
                
                placed += 1
                obj_counter = min(len(obj_type_list)-1, obj_counter+1)
                obj_type = obj_type_list[obj_counter]
        
        return

    def place_groups(
        self, 
        points_manager: PointManager,
        map_layer_type: MapLayerType, 
        obj_type_list = DEFAULT_OBJECT_TYPES,
        player_id: PlayerId = DEFAULT_PLAYER,
        groups: int = 1,
        group_size: int = 1,
        group_density: int = None,
        groups_density: int = None,
        clumping: int = 0,
        clumping_func: Callable = None, 
        margin: int = 0,
        start_point: tuple = (-1,-1),
        ghost_margin: bool = True,
        ):
        """
        Places multiple groups of objects.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            obj_type: The type of object to be placed.
            player_id: Id of the object to be placed.
            margin: Margin between each object and any other object.
            group_size: Number of members per group.
            groups: Number of groups.
            clumping: How clumped the group members are. 0 is totally clumped. Higher numbers spread members out.
            ghost_margin: Option to include ghost margins, ie. change neighboring squares so nothing can use them.
        """

        # Checks the object types are valid and converts to a list if needed.
        if type(obj_type_list) != list:
            obj_type_list = [obj_type_list]

        if len(obj_type_list) == 0:
            raise ValueError("Object type list \'{obj_type_list}\' has no entries.")
                
        if groups_density is not None:
            groups = groups_density*len(points_manager.get_point_list())//2000
            groups = int(groups)
        
        for i in range(groups):
            self._place_group(
                point_manager=points_manager,
                map_layer_type=map_layer_type, 
                obj_type_list=obj_type_list, 
                player_id=player_id,
                group_size=group_size,
                group_density=group_density,
                clumping=clumping,  
                clumping_func=clumping_func,
                margin=margin,
                start_point=start_point,
                ghost_margin=ghost_margin, 
                )


    # ---------------------------- HELPER METHODS ----------------------------------
    
    def _distance_to_edge(self, points, point):
        """
        Finds distance to edge blocks.

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
        """
        x, y = point

        for dist in range(1,100):
            for i in range(-dist,dist+1):
                for j in range(-dist,dist+1):
                    if not (x+i,y+j) in points:
                        return dist

        return 100