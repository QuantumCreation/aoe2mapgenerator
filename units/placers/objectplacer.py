
import random
from re import A
from site import abs_paths
from telnetlib import GA
from typing import Union
from numpy import place

from pandas import array
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from map.map_utils import MapUtilsMixin
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize, Directions, ValueType, GateTypes
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from copy import deepcopy



class PlacerMixin(MapUtilsMixin):
    """
    TODO
    """

    # By default the object is placed in the first value from the value_type list.
    def _place_group(
        self, 
        value_types: list[ValueType], 
        array_space_types: list[Union[int, tuple]], 
        obj_types: list = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER,
        group_size: int = 1,
        clumping: int = 1,
        margin: int = 0, 
        start_point: tuple = (-1,-1),
        ghost_margin: bool = True,
        place_on_n_maps: int = 1,
        ):
        """
        Places a single group of units on a specific array space.

        Args:
            value_type: The map type.
            array_space_type: Array space id to get points for.
            obj_type: The type of object to be placed.
            player_id: Id of the object to be placed.
            margin: Margin between each object and any other object.
            group_size: Number of members per group.
            clumping: How clumped the group members are. 0 is totally clumped. Higher numbers spread members out.
            ghost_margin: Option to include ghost margins, ie. change neighboring squares so nothing can use them.
            place_on_n_maps: Places group on the first n maps corresponding to the value types.
        """
        # Finds the smallest dict so that when looking for spots to place objects, we
        # minimize the total number of points looked at.
        
        smallest_dict_index, smallest_dict = self._get_dict_with_min_members(value_types, array_space_types)
        points_list = list(smallest_dict[array_space_types[smallest_dict_index]])

        if type(start_point) != tuple or start_point[0] < 0 or start_point[1] < 0:
            start_point = points_list[int(random.random()*len(points_list))]
        
        obj_counter = 0
        obj_type = obj_types[obj_counter]
        placed = 0

        # List of values we look through is based off of our smallest dict points, optimizing performance.
        for (x,y) in sorted(points_list, key = lambda point: ((point[0]-start_point[0])**2 + (point[1]-start_point[1])**2 + random.random()*((clumping)**2))):

            if placed >= group_size:
                return
            
            if self._check_placement(value_types, array_space_types, (x,y), obj_type, margin):
                # Only places values on the the first n maps
                self._place(value_types[:place_on_n_maps], (x,y), obj_type, player_id, margin, ghost_margin)
                
                placed += 1
                obj_counter = min(len(obj_types)-1, obj_counter+1)
                obj_type = obj_types[obj_counter]

        return

    def place_groups(
        self, 
        value_types: list[ValueType], 
        array_space_types: list[Union[int, tuple]], 
        obj_types = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER,
        groups: int = 1,
        group_size: int = 1,
        clumping: int = 0, 
        margin: int = 0,
        start_point: tuple = (-1,-1),
        ghost_margin: bool = True,
        place_on_n_maps: int = 1,
        ):
        """
        Places multiple groups of objects.

        Args:
            value_type: The map type.
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
        if type(value_types) != list:
            value_types = [value_types]

        if len(value_types) == 0:
            return

        # Checks the array space types are valid and converts to a list if needed.
        if type(array_space_types) != list:
            array_space_types = [array_space_types]

        if len(array_space_types) == 0:
            return

        # Checks the object types are valid and converts to a list if needed.
        if type(obj_types) != list:
            obj_types = [obj_types]

        if len(obj_types) == 0:
            return
        
        if len(value_types) != len(array_space_types):
            raise ValueError("Length of value types list and array space types not equal.")


        # Checks that each map value type actually includes the correct array space type, otherwise stop.
        for value_type, array_space_type in zip(value_types, array_space_types):
            if array_space_type not in self.get_dictionary_from_value_type(value_type):
                return
                print(f"The {value_type} array does not contain any value with {array_space_type}.")
                
        for i in range(groups):
            self._place_group(
                value_types = value_types, 
                array_space_types = array_space_types, 
                obj_types = obj_types, 
                player_id = player_id,
                group_size = group_size,
                clumping = clumping,  
                margin = margin,
                start_point=start_point,
                ghost_margin = ghost_margin, 
                place_on_n_maps = place_on_n_maps,
                )

    # Multiple map type functionality still seems a bit weird to me. May refactor later.
    def add_borders(
        self, 
        value_types: list[ValueType], 
        array_space_type: Union[int, tuple], 
        border_type,
        margin: int, 
        player_id: PlayerId = DEFAULT_PLAYER
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            array: Array of the complete map space.
            value_type: The map type.
            array_space_type: Array space id to get points for.
            border_type: Type of border to place.
            margin: Type of margin to place.
            player_id: Id of the objects being placed.
        """
        # Checks the value types are valid and converts to a list if needed.
        if type(value_types) != list:
            value_types = [value_types]

        if len(value_types) == 0:
            return
        
        dictionary = self.get_dictionary_from_value_type(value_types[0])

        if array_space_type not in dictionary:
            return

        points = dictionary[array_space_type].copy()

        # Uses only the first value type and array space to find where to place points. May change later.
        # Still places the points in every space.
        for value_type in value_types:
            for point in points:
                if self._is_on_border(points, point, margin):
                    x, y = point
                    self.set_point(x,y,border_type, value_type, player_id)
        
        return
    
    # SOMETHING SOMETIMES LEADS TO MASSIVE PERFORMANCE PROBLEMS HERE. IDK WHAT LOL.
    def add_borders_all(
        self, 
        value_types: list[ValueType],
        border_type, 
        margin: int = 1, 
        player_id: PlayerId = DEFAULT_PLAYER
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            value_type: The map type.
            border_type: Type of border to place.
            margin: Type of margin to place.
            player_id: Id of the objects being placed.
        """
        all_array_space_types = list(set_from_matrix(self.get_array_from_value_type(value_types[0])))

        for space_type in all_array_space_types:
            self.add_borders(value_types, space_type, border_type, margin, player_id=player_id)
        
        return

    # ---------------------------- HELPER METHODS ----------------------------------

    def _check_placement(  
        self,
        value_types: list[ValueType], 
        array_space_types: list[Union[int, tuple]], 
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
        for value_type, array_space_type in zip(value_types, array_space_types):
            obj_space = self.get_dictionary_from_value_type(value_type)[array_space_type]

            for i in range(-margin, eff_width):
                for j in range(-margin, eff_height):
                    if (x+i, y+j) not in obj_space:
                        return False
        
        return True

    def _place(
        self, 
        value_types: ValueType, 
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
            value_type: The map type.
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

        for value_type in value_types:
            # IDK but this if statement may speed things up a little bit. NEEDS TESTING.
            if width > 1 or height > 1 or margin > 0:
                for i in range(-margin, eff_width):
                    for j in range(-margin, eff_height):
                        if 0<=i<width and 0<=j<height:
                            self.set_point(x+i,y+j,GHOST_OBJECT_DISPLACEMENT, value_type, player_id)
                        elif ghost_margin:
                            self.set_point(x+i,y+j,GHOST_OBJECT_MARGIN, value_type, player_id)
        
            self.set_point(x+width//2, y+height//2, obj_type, value_type, player_id)

        return

    def _is_on_border(self, points, point, margin):
        """
        Checks if given point is on a border

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
            margin: Number of squares to fill in along the edge.
        """
        x, y = point

        for i in range(-margin,margin+1):
            for j in range(-abs(abs(i)-margin),abs(abs(i)-margin)+1):
                if not (x+i,y+j) in points:
                    return True

        return False

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

    # ----------------------------- GATE PLACEMENT ----------------------------------

    def place_gate_on_four_sides(
        self, 
        value_types: list[ValueType], 
        array_space_types: list[Union[int, tuple]], 
        gate_type: GateTypes, 
        player_id: PlayerId = DEFAULT_PLAYER,
        place_on_n_maps: int = 1,
        ):
        """
        Takes the average location of points in the given array space, and places gates on four sides.

        Args:
            value_type: The map type.
            array_space_type: Array space id to get points for.
            gate_type: Type of the gate being placed
            playerId: Id of the objects being placed.
        """
        # ALL OF THESE CHECKS SHOULD PROBABLY BE ABSTRACTED AWAY ELSEWHERE
        # Checks the value types are valid and converts to a list if needed.
        if type(value_types) != list:
            value_types = [value_types]

        if len(value_types) == 0:
            return

        # Checks the array space types are valid and converts to a list if needed.
        if type(array_space_types) != list:
            array_space_types = [array_space_types]

        if len(array_space_types) == 0:
            return
        
        if len(value_types) != len(array_space_types):
            raise ValueError("Length of value types list and array space types not equal.")


        # Checks that each map value type actually includes the correct array space type, otherwise stop.
        for value_type, array_space_type in zip(value_types, array_space_types):
            if array_space_type not in self.get_dictionary_from_value_type(value_type):
                return
                print(f"The {value_type} array does not contain any value with {array_space_type}.")
        
        avg_point = self._get_average_point_position(value_types, array_space_types)

        for direction in [direction.value for direction in Directions]:
            point = self._get_first_point_in_given_direction(value_types, array_space_types, avg_point, direction)

            if point is None:
                continue

            self._place_gate_closest_to_point(value_types, array_space_types, gate_type, point, player_id, place_on_n_maps)

    # --------------------------- GATE HELPER METHODS ---------------------------------

    def _get_average_point_position(self, value_types, array_space_types):
        """
        TODO
        """
        total_points = 0
        totx = 0
        toty = 0

        smallest_dict_index, smallest_dict = self._get_dict_with_min_members(value_types, array_space_types)

        for point in smallest_dict[array_space_types[smallest_dict_index]]:
            if self._check_placement(value_types, array_space_types, point, None,0,width=1,height=1):
                total_points += 1
                totx += point[0]
                toty += point[1]

        return (totx//total_points, toty//total_points)
    
    def _get_dict_with_min_members(self, value_types, array_spave_types):
        """
        TODO
        """
        list_of_dictionary_tuples = ((i, self.get_dictionary_from_value_type(value_type)) for i, value_type in enumerate(value_types))
        smallest_dict_index, smallest_dict = min(list_of_dictionary_tuples, key = lambda tuple: len(tuple[1]))

        return smallest_dict_index, smallest_dict

    def _get_first_point_in_given_direction(
        self, 
        value_types: list[ValueType], 
        array_space_types,
        starting_point: tuple,
        direction: Directions
        ):
        """
        Finds the first point in the matching array space type with the given direction.

        Args:
            value_type: The map type.
            array_space_type: Array space id to get points for.
            starting_point: Point to start searching from.
            direciton: Direction to search in.
        """
        point = starting_point

        smallest_dict_index, smallest_dict = self._get_dict_with_min_members(value_types, array_space_types)
        points = smallest_dict[array_space_types[smallest_dict_index]]

        # NOTE THIS CAN BE OPTIMIZED BY STARTING AT THE GIVEN POINT AND NOT GOING BEYOND MAP BOUNDARIES
        # IT CURRENTLY RUNS THE FULL LENGTH OF THE MAP NO MATTER WHAT.
        for i in range(self.size):

            if point in points:
                if self._check_placement(value_types, array_space_types,point,None,0,width=1,height=1):
                    return point

            next_point = tuple(map(sum, zip(point, direction)))
            point = next_point
        
        return None

    # Maybe this and the other place method could be joined or simplified somehow.
    def _place_gate_closest_to_point(
        self, 
        value_types: ValueType, 
        array_space_types, 
        gate_type: GateTypes, 
        starting_point, 
        player_id: PlayerId,
        place_on_n_maps: int = 1,
        ):
        """
        TODO
        """
        smallest_dict_index, smallest_dict = self._get_dict_with_min_members(value_types, array_space_types)
        points_list = smallest_dict[array_space_types[smallest_dict_index]]

        for (x,y) in sorted(points_list, key = lambda point: ((point[0]-starting_point[0])**2 + (point[1]-starting_point[1])**2)):
            obj_type = None

            if self._check_placement(value_types, array_space_types, (x,y), obj_type, margin = 0, width = 1, height = 4):
                obj_type = BuildingInfo[gate_type.value[2]]
                self._place(value_types[:place_on_n_maps], (x,y), obj_type, player_id, margin=0, ghost_margin=0, width = 1, height = 4)
                return

            if self._check_placement(value_types, array_space_types, (x,y), obj_type, margin = 0, width = 4, height = 1):
                obj_type = BuildingInfo[gate_type.value[3]]
                self._place(value_types[:place_on_n_maps], (x,y), obj_type, player_id, margin=0, ghost_margin=0, width = 4, height = 1)
                return
        
        return



