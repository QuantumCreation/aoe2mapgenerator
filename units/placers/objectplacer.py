
import random
from re import A
from site import abs_paths
from telnetlib import GA
from typing import Union, Callable
from xml.dom import ValidationErr
import numpy as np

from pandas import array
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from map.map_utils import MapUtilsMixin
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize, Directions, MapLayerType, GateTypes, CheckPlacementReturnTypes
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from copy import deepcopy
import functools
from time import time
from collections import deque
from heapq import nsmallest

class PlacerMixin(MapUtilsMixin):
    """
    TODO
    """

    # By default the object is placed in the first value from the map_layer_type list.
    def _place_group(
        self, 
        map_layer_type_list: list[MapLayerType], 
        array_space_type_list: list[Union[int, tuple]], 
        obj_type_list: list = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER,
        group_size: int = 1,
        group_density: int = None,
        clumping: int = 1,
        clumping_func: Callable = None,
        margin: int = 0, 
        start_point: tuple = (-1,-1),
        ghost_margin: bool = True,
        place_on_n_maps: int = 1,
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
        
        if clumping_func is None:
            clumping_func = self.default_clumping_func

        # Get the intersection of the specified value types and array spaces
        s = self.get_intersection_of_spaces(map_layer_type_list, array_space_type_list)
        points_list = list(s)
        if len(points_list) == 0:
            return
        
        # Adjust group size based on density if specified
        if group_density is not None:
            group_size = group_density*len(points_list)//100

        # Choose a random start point if none is specified or invalid
        if type(start_point) != tuple or start_point[0] < 0 or start_point[1] < 0:
            start_point = points_list[int(random.random()*len(points_list))]

            
        

        # Start with some size as the default
        total_size = 1
        effmargin = (1 + margin) if ghost_margin else margin

        if clumping == -1:
            total_size = (self.size + 100)**2
        else:
            for i in range(len(obj_type_list)):
                total_size += (ObjectSize(obj_type_list[i]._name_).value + effmargin)**2

            if group_size > len(obj_type_list):
                total_size += (group_size-len(obj_type_list))*(ObjectSize(obj_type_list[-1]._name_).value + effmargin)**2
        
        world_partition_sets = self.get_world_partition(start_point, total_size, clumping)
        points_list = [list(set.intersection(s, wpset)) for wpset in world_partition_sets]
        points_list = functools.reduce(lambda acc, lst: acc + lst, points_list)

        # Sort the points based on clumping score if group size is in a certain range
        if 1<group_size<len(points_list):
            # points_list = nsmallest(group_size, 
            #                         points_list, 
            #                         key = lambda x: clumping_func(x, start_point, clumping))
            points_list = sorted(points_list, key = lambda point: clumping_func(point, start_point, clumping))


        # Try to place objects on the selected points
        obj_counter = 0
        obj_type = obj_type_list[obj_counter]
        placed = 0

        for (x,y) in points_list:
            if placed >= group_size:
                return
            
            status = self._check_placement(map_layer_type_list, array_space_type_list, (x,y), obj_type, margin)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return
    
            if status == CheckPlacementReturnTypes.SUCCESS:
                # Place the object on the first n maps
                self._place(map_layer_type_list[:place_on_n_maps], (x,y), obj_type, player_id, margin, ghost_margin)
                
                placed += 1
                obj_counter = min(len(obj_type_list)-1, obj_counter+1)
                obj_type = obj_type_list[obj_counter]
        
        return

    def place_groups(
        self, 
        map_layer_type_list: list[MapLayerType], 
        array_space_type_list: list[Union[int, tuple]], 
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
        place_on_n_maps: int = 1,
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

        # Checks the value types are valid and converts to a list if needed.
        if type(map_layer_type_list) != list:
            map_layer_type_list = [map_layer_type_list]

        if len(map_layer_type_list) == 0:
            raise ValueError("Value type list \'{map_layer_type_list}\' has no entries.")

        # Checks the array space types are valid and converts to a list if needed.
        if type(array_space_type_list) != list:
            array_space_type_list = [array_space_type_list]

        if len(array_space_type_list) == 0:
            raise ValueError("Array space type list \'{array_space_type_list}\' has no entries.")

        # Checks the object types are valid and converts to a list if needed.
        if type(obj_type_list) != list:
            obj_type_list = [obj_type_list]

        if len(obj_type_list) == 0:
            raise ValueError("Object type list \'{obj_type_list}\' has no entiries.")
        
        if len(map_layer_type_list) != len(array_space_type_list):
            raise ValueError("Length of value types list and array space types not equal.")


        # Checks that each map value type actually includes the correct array space type, otherwise stop.
        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
            if array_space_type not in self.get_dictionary_from_map_layer_type(map_layer_type):
                # raise ValueError(f"The value {array_space_type} is not present in the {map_layer_type} map.")
                print(f"The value {array_space_type} is not present in the {map_layer_type} map.")
                return
                
        if groups_density is not None:
            groups = groups_density*len(self.get_intersection_of_spaces(map_layer_type_list,array_space_type_list))//2000
            groups = int(groups)
        
        for i in range(groups):
            self._place_group(
                map_layer_type_list=map_layer_type_list, 
                array_space_type_list=array_space_type_list, 
                obj_type_list=obj_type_list, 
                player_id=player_id,
                group_size=group_size,
                group_density=group_density,
                clumping=clumping,  
                clumping_func=clumping_func,
                margin=margin,
                start_point=start_point,
                ghost_margin=ghost_margin, 
                place_on_n_maps=place_on_n_maps,
                )

    # Multiple map type Callableality still seems a bit weird to me. May refactor later.
    def add_borders(
        self, 
        map_layer_type_list: list[MapLayerType], 
        array_space_type_list: Union[int, tuple], 
        obj_type,
        margin: int = 1, 
        player_id: PlayerId = DEFAULT_PLAYER,
        place_on_n_maps: int = 1,
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            obj_type: The type of object to be placed.
            margin: Type of margin to place.
            player_id: Id of the objects being placed.
            place_on_n_maps: Number of maps to place the objects on.
        """
        # Checks the value types are valid and converts to a list if needed.
        if type(map_layer_type_list) != list:
            map_layer_type_list = [map_layer_type_list]

        if len(map_layer_type_list) == 0:
            raise ValueError("No elements in value type list.")

        if type(array_space_type_list) != list:
            array_space_type_list = [array_space_type_list]

        points = self.get_intersection_of_spaces(map_layer_type_list, array_space_type_list).copy()
 
        # Uses only the first value type and array space to find where to place points. May change later.
        # Still places the points in every space.

        for point in points:
            if self._is_on_border(points, point, margin):
                for map_layer_type in map_layer_type_list[:place_on_n_maps]:
                    x, y = point
                    self.set_point(x,y,obj_type, map_layer_type, player_id)
           
        return
    
    # SOMETHING SOMETIMES LEADS TO MASSIVE PERFORMANCE PROBLEMS HERE. IDK WHY LOL.
    def add_borders_all(
        self, 
        map_layer_type_list: list[MapLayerType],
        array_space_type_list: Union[int, tuple],
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
                map_layer_type_list, 
                array_space_type_list, 
                border_type, 
                margin, 
                player_id=player_id, 
                place_on_n_maps=place_on_n_maps
                )

        return

    # ---------------------------- HELPER METHODS ----------------------------------

    def _check_placement(  
        self,
        map_layer_type_list: list[MapLayerType], 
        array_space_type_list: list[Union[int, tuple]], 
        point: tuple,
        obj_type = None, 
        margin: int = 0,
        width: int = -1,
        height: int = -1):
        """
        Checks if the given point is a valid placement for an object.

        Args:
            obj_space: Set containing all possible points within a cell.
            point: X and y coordinates for where the object is attempting to be placed.
            obj_type: The type of object to be placed.
            margin: Margin between object placements.
            width: TBD
            height: TBD
        """

        if height <= 0 or width <= 0:
            if obj_type is None:
                return False
            obj_size = ObjectSize(obj_type._name_).value
            width = obj_size
            height = obj_size

        eff_width = width + margin
        eff_height = height + margin

        x, y = point
        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
            try:
                obj_space = self.get_dictionary_from_map_layer_type(map_layer_type)[array_space_type]
            except:
                return CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE
            
            for i in range(-margin, eff_width):
                for j in range(-margin, eff_height):
                    if (x+i, y+j) not in obj_space:
                        return CheckPlacementReturnTypes.FAIL
        
        return CheckPlacementReturnTypes.SUCCESS

    def _place(
        self, 
        map_layer_type_list: MapLayerType, 
        point: tuple, 
        obj_type, 
        player_id: PlayerId, 
        margin: int, 
        ghost_margin: bool, 
        height: int = -1, 
        width: int = -1):
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
        

        if height <= 0 or width <= 0:
            if obj_type is None:
                return False
            obj_size = ObjectSize(obj_type._name_).value
            width = obj_size
            height = obj_size

        eff_width = width + margin
        eff_height = height + margin
        
        x, y = point

        for map_layer_type in map_layer_type_list:
            # IDK but this if statement may speed things up a little bit. NEEDS TESTING.
            if width > 1 or height > 1 or margin > 0 or ghost_margin:
                for i in range(-margin, eff_width):
                    for j in range(-margin, eff_height):
                        if 0<=i<width and 0<=j<height:
                            self.set_point(x+i,y+j,GHOST_OBJECT_DISPLACEMENT, map_layer_type, player_id)
                        elif ghost_margin:
                            self.set_point(x+i,y+j,GHOST_OBJECT_MARGIN, map_layer_type, player_id)
        
            self.set_point(x+width//2, y+height//2, obj_type, map_layer_type, player_id)

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
    
    def _get_set_with_min_members(self, map_layer_type_list, array_space_type_list):
        """
        Gets the dict with the minimum members from the given value type list and array space type list.
        """
        all_sets = (self.get_dictionary_from_map_layer_type(map_layer_type)[array_space_type] for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list))
        min_set = min(all_sets, key = lambda s: len(s))

        return min_set

    def _get_random_element_from_list(self, lst):
        """
        Gets a random element from a list.
        
        Args:
            lst: A list.
        """
        return lst[int(random.random())*len(lst)]

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
    # ---------------------------- SORTING FUNCTIONS ----------------------------

    def default_clumping_func(self, p1, p2, clumping):
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

    # ----------------------------- GATE PLACEMENT ----------------------------------

    def place_gate_on_four_sides(
        self, 
        map_layer_type_list: list[MapLayerType], 
        array_space_type_list: list[Union[int, tuple]], 
        gate_type: GateTypes, 
        player_id: PlayerId = DEFAULT_PLAYER,
        place_on_n_maps: int = 1,
        ):
        """
        Takes the average location of points in the given array space, and places gates on four sides.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            gate_type: Type of the gate being placed
            playerId: Id of the objects being placed.
        """
        # ALL OF THESE CHECKS SHOULD PROBABLY BE ABSTRACTED AWAY ELSEWHERE
        # Checks the value types are valid and converts to a list if needed.
        if type(map_layer_type_list) != list:
            map_layer_type_list = [map_layer_type_list]

        if len(map_layer_type_list) == 0:
            raise ValueError("Value type list \'{map_layer_type_list}\' has no entries.")


        # Checks the array space types are valid and converts to a list if needed.
        if type(array_space_type_list) != list:
            array_space_type_list = [array_space_type_list]

        if len(array_space_type_list) == 0:
            raise ValueError("Array space type list \'{array_space_type_list}\' has no entries.")
        
        if len(map_layer_type_list) != len(array_space_type_list):
            raise ValueError("Length of value types list and array space types not equal.")


        # Checks that each map value type actually includes the correct array space type, otherwise stop.
        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
            if array_space_type not in self.get_dictionary_from_map_layer_type(map_layer_type):
                print(f"The value {array_space_type} is not present in the {map_layer_type} map.")
                return
        
        avg_point = self._get_average_point_position(map_layer_type_list, array_space_type_list)

        for direction in [direction.value for direction in Directions]:
            point = self._get_first_point_in_given_direction(map_layer_type_list, array_space_type_list, avg_point, direction)

            if point is None:
                print(f"No point found in the {direction} direction.")
                continue

            self._place_gate_closest_to_point(map_layer_type_list, array_space_type_list, gate_type, point, player_id, place_on_n_maps)

    # --------------------------- GATE HELPER METHODS ---------------------------------

    def _get_average_point_position(self, map_layer_type_list, array_space_type_list):
        """
        Gets the location of the average point from the given value type and array space lists.
        """
        total_points = 0
        totx = 0
        toty = 0

        smallest_set = self._get_set_with_min_members(map_layer_type_list, array_space_type_list)

        for point in smallest_set:
            status = self._check_placement(map_layer_type_list, array_space_type_list, point, None,0,width=1,height=1)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return (0,0)

            if status == CheckPlacementReturnTypes.SUCCESS:
                total_points += 1
                totx += point[0]
                toty += point[1]

        return (totx//total_points, toty//total_points)
    
    def _get_first_point_in_given_direction(
        self, 
        map_layer_type_list: list[MapLayerType], 
        array_space_type_list,
        starting_point: tuple,
        direction: Directions
        ):
        """
        Finds the first point in the matching array space type with the given direction.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            starting_point: Point to start searching from.
            direciton: Direction to search in.
        """
        point = starting_point

        smallest_set = self._get_set_with_min_members(map_layer_type_list, array_space_type_list)
        points = smallest_set

        # NOTE THIS CAN BE OPTIMIZED BY STARTING AT THE GIVEN POINT AND NOT GOING BEYOND MAP BOUNDARIES
        # IT CURRENTLY RUNS THE FULL LENGTH OF THE MAP NO MATTER WHAT.
        for i in range(self.size):

            if point in points:
                status = self._check_placement(map_layer_type_list, array_space_type_list,point,None,0,width=1,height=1)

                if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                    return None

                if status == CheckPlacementReturnTypes.SUCCESS:
                    return point

            next_point = tuple(map(sum, zip(point, direction)))
            point = next_point
        
        return None

    # Maybe this and the other place method could be joined or simplified somehow.
    def _place_gate_closest_to_point(
        self, 
        map_layer_type_list: MapLayerType, 
        array_space_type_list, 
        gate_type: GateTypes, 
        starting_point, 
        player_id: PlayerId,
        place_on_n_maps: int = 1,
        ):
        """
        Places a gate as close as possible to the starting point.
        """
        points_set = self.get_intersection_of_spaces(map_layer_type_list, array_space_type_list)

        for (x,y) in sorted(points_set, key = lambda point: ((point[0]-starting_point[0])**2 + (point[1]-starting_point[1])**2)):

            status = self._check_placement(map_layer_type_list, array_space_type_list, (x,y), margin = 0, width = 1, height = 4)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return

            if status == CheckPlacementReturnTypes.SUCCESS:
                obj_type = BuildingInfo[gate_type.value[2]]
                self._place(map_layer_type_list[:place_on_n_maps], (x,y), obj_type, player_id, margin=0, ghost_margin=0, width = 1, height = 4)
                return

            status = self._check_placement(map_layer_type_list, array_space_type_list, (x,y), margin = 0, width = 4, height = 1)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return

            if status == CheckPlacementReturnTypes.SUCCESS:
                obj_type = BuildingInfo[gate_type.value[3]]
                self._place(map_layer_type_list[:place_on_n_maps], (x,y), obj_type, player_id, margin=0, ghost_margin=0, width = 4, height = 1)
                return
        
        return



