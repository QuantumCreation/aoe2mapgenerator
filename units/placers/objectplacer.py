
import random
from re import A
from site import abs_paths
from telnetlib import GA
from typing import Union

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

    def place_all(
        self, 
        value_type: ValueType, 
        array_space_type: Union[int, tuple], 
        obj_types: list = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER,
        margin: int = 0, 
        total: int = 1,
        ghost_margin: bool = True
        ):
        """
        Places n number of objects randomly.

        Args:
            map: Map object with the corresponding array and set of points.
            array_space_type: Array space id to get points for.
            obj_type: The type of object to be placed.
            margin: Area around the object to be placed.
            total: Total number of objects to place.
            ghost_margin: Option to include ghost margins, ie. change neighboring squares so nothing can use them.
        """
        if type(obj_types) != list:
            obj_types = [obj_types]
        
        if len(obj_types) == 0:
            return
        
        obj_counter = 0
        obj_type = obj_types[obj_counter]

        for i in range(total):

            if not self._check_and_place(value_type, array_space_type, obj_type, player_id, margin, ghost_margin):
                return

            obj_counter = min(len(obj_types)-1, obj_counter+1)
            obj_type = obj_types[obj_counter]
        
        return

    def place_group(
        self, 
        value_type: ValueType, 
        array_space_type: Union[int, tuple], 
        obj_types: list = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER, 
        margin: int = 0, 
        group_size: int = 1, 
        clumping: int = 1,
        ghost_margin: bool = True,
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
        """
        dictionary = self.get_dictionary_from_value_type(value_type)

        if array_space_type in dictionary:
            points = dictionary[array_space_type]
        else:
            return 

        points_list = list(points)
        (xrand, yrand) = points_list[int(random.random()*len(points))]
        
        if type(obj_types) != list:
            obj_types = [obj_types]

        if len(obj_types) == 0:
            return
        
        obj_counter = 0
        obj_type = obj_types[obj_counter]
        placed = 0
        for (x,y) in sorted(points_list, key = lambda a: ((a[0]-xrand)**2 + (a[1]-yrand)**2 + random.random()*((clumping)**2))):

            if placed >= group_size:
                return

            if self._check_placement(points, (x,y), obj_type, margin=margin):
                self._place(value_type, (x,y), obj_type, player_id, margin, ghost_margin)
                
                placed += 1
                obj_counter = min(len(obj_types)-1, obj_counter+1)
                obj_type = obj_types[obj_counter]

        return

    def place_groups(
        self, 
        value_type: ValueType, 
        array_space_type: Union[int, tuple], 
        obj_types = DEFAULT_OBJECT_TYPES, 
        player_id: PlayerId = DEFAULT_PLAYER, 
        margin: int = 0, 
        group_size: int = 1, 
        groups: int = 1, 
        clumping: int = 1,
        ghost_margin: bool = True,
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

        if type(obj_types) != list:
            obj_types = [obj_types]

        if len(obj_types) == 0:
            return
        
        for i in range(groups):
            self.place_group(value_type, array_space_type, obj_types, player_id, margin, group_size, clumping, ghost_margin)

    def add_borders(
        self, 
        value_type: ValueType, 
        array_space_type: Union[int, tuple], 
        border_type,
        border_margin: int, 
        player_id: PlayerId = DEFAULT_PLAYER
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            array: Array of the complete map space.
            array_space_type: Array space id to get points for.
            border_type: Type of border to place.
            border_margin: Type of margin to place.
            player_id: Id of the objects being placed.
        """
        dictionary = self.get_dictionary_from_value_type(value_type)

        if array_space_type in dictionary:
            points = dictionary[array_space_type].copy()
        else:
            return

        for point in points:
            if self._is_on_border(points, point, border_margin):
                x, y = point
                self.set_point(x,y,border_type, value_type, player_id)
        
        return
    
    # SOMETHING LEADS TO MASSIVE PROBLEMS HERE. IDK WHAT LOL.
    def add_borders_all(
        self, 
        value_type: ValueType, 
        border_type, 
        border_margin: int, 
        player_id: PlayerId = DEFAULT_PLAYER
        ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            array: Array of the complete map space.
            array_space_type: Array space id to get points for.
            border_type: Type of border to place.
            border_margin: Type of margin to place.
            player_id: Id of the objects being placed.
        """
        all_array_space_types = list(set_from_matrix(self.get_array_from_value_type(value_type)))

        for space_type in all_array_space_types:
            self.add_borders(value_type, space_type, border_type, border_margin, player_id=player_id)
        
        return

    # ----------------------- HELPER METHODS --------------------------

    def _check_placement(self, obj_space, point, obj_type = None, margin = 0, width = -1, height = -1):
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
        # SOMETHING NEEDS TO BE CHANGED HERE
        

        if height >=  1 and width >= 1:
            eff_width = width + margin
            eff_height = height + margin
        else:
            if obj_type is None:
                return False
            obj_size = ObjectSize(obj_type._name_).value
            eff_width = obj_size + margin
            eff_height = obj_size + margin

        x, y = point

        for i in range(-margin, eff_width):
            for j in range(-margin, eff_height):
                if (x+i,y+j) not in obj_space:
                    return False
        
        return True

    def _place(self, value_type, point, obj_type, player_id, margin, ghost_margin, height = -1, width = -1):
        """
        Places a single object. Assumes placement has already been verified.

        Args:
            map: Map object with the corresponding array and set of points.
            point: Point to place base of object.
            obj_type: The type of object to be placed.
            margin: Area around the object to be placed.
        """
        

        if height >=  1 and width >= 1:
            eff_width = width + margin
            eff_height = height + margin
        else:
            obj_size = ObjectSize(obj_type._name_).value
            eff_width = obj_size + margin
            eff_height = obj_size + margin
        
        x, y = point

        for i in range(-margin, eff_width):
            for j in range(-margin, eff_height):
                if 0<=i<obj_size and 0<=j<obj_size:
                    self.set_point(x+i,y+j,GHOST_OBJECT_DISPLACEMENT, value_type, player_id)
                elif ghost_margin:
                    self.set_point(x+i,y+j,GHOST_OBJECT_MARGIN, value_type, player_id)
        
        self.set_point(x+obj_size//2, y+obj_size//2, obj_type, value_type, player_id)

        return
            
    def _check_and_place(self, value_type, array_space_type, player_id, obj_type, margin, ghost_margin):
        """
        Finds an open space and then places an object.

        Args:
            map: Map object with the corresponding array and set of points.
            array_space_type: Array space id to get points for.
            player_id: Id of the objects being placed.
            obj_type: The type of object to be placed.
            margin: Area around the object to be placed.
        """
        dictionary = self.get_dictionary_from_value_type(value_type)

        if array_space_type in dictionary:
            points = dictionary[array_space_type]
        else:
            return False

        for (x,y) in sorted(points, key = lambda _: random.random()):
            if self._check_placement(value_type, points, (x,y), obj_type, margin=margin):
                self._place(self, value_type, (x,y), player_id, obj_type, margin, ghost_margin)
                return True
        
        return False

    """
    DEPRECATED
    """
    def _distance_to_edge(self, points, point):
        """
        Finds distance to edge blocks

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

    def _is_on_border(self, points, point, border_margin):
        """
        Checks if given point is on a border

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
            border_margin: Number of squares to fill in along the edge.
        """
        x, y = point

        for i in range(-border_margin,border_margin+1):
            for j in range(-abs(abs(i)-border_margin),abs(abs(i)-border_margin)+1):
                if not (x+i,y+j) in points:
                    return True

        return False

    """
    DEPRECATED
    """
    def _get_valid_points(self, array, array_space_type):
        """
        Retruns a set of points with a matching space type.

        Args:
            array: Array of the complete map space.
            array_space_type: Array space id to get points for.
        """
        possible = set()

        for i in range(len(array)):
            for j in range(len(array[0])):
                if array[i][j] == array_space_type:
                    possible.add((i,j))
        
        return possible
    

    # ------------------------------- GATE PLACEMENT -------------------


    def place_gate_on_four_sides(self, value_type, array_space_type, gate_type, player_id = DEFAULT_PLAYER):
        """
        TODO
        """
        dictionary = self.get_dictionary_from_value_type(value_type)

        if not array_space_type in dictionary:
            return
        
        totx = 0
        toty = 0
        length = len(dictionary[array_space_type])

        for i, (x,y) in enumerate(dictionary[array_space_type]):
            totx += x
            toty += y
        
        avg_point = (totx//length, toty//length)

        for direction in [direction.value for direction in Directions]:
            point = self._get_first_point_in_given_direction(value_type, array_space_type, avg_point, direction)

            if point is None:
                continue

            self._place_gate_closest_to_point(value_type, array_space_type, gate_type, point, player_id)


    def _get_first_point_in_given_direction(self, value_type: ValueType, array_space_type, starting_point, direction: Directions):
        """
        Finds the first point in the matching array space type with the given direction.

        Args:
            value_type: The map type.
            array_space_type: Array space id to get points for.
            starting_point: Point to start searching from.
            direciton: Direction to search in.
        """
        point = starting_point

        dictionary = self.get_dictionary_from_value_type(value_type)

        if array_space_type in dictionary:
            points = dictionary[array_space_type]
        else:
            return

        # NOTE THIS CAN BE OPTIMIZED BY STARTING AT THE GIVEN POINT AND NOT GOING BEYOND MAP BOUNDARIES
        # IT CURRENTLY RUNS THE FULL LENGTH OF THE MAP NO MATTER WHAT.
        for i in range(self.size):

            if point in points:
                return point

            next_point = tuple(map(sum, zip(point, direction)))
            point = next_point
        
        return None


    def _place_gate_closest_to_point(self, value_type, array_space_type, gate_type, point, player_id):
        """
        TODO
        """
        dictionary = self.get_dictionary_from_value_type(value_type)

        points_list = list(dictionary[array_space_type])

        if array_space_type in dictionary:
            points = dictionary[array_space_type]
        else:
            return

        for (x,y) in sorted(points_list, key = lambda a: ((a[0]-point[0])**2 + (a[1]-point[1])**2)):
            obj_type = None

            if self._check_placement(points, (x,y), obj_type, margin = 0, width = 4, height = 1):
                obj_type = BuildingInfo[gate_type.value[3]]
                self._place(value_type, (x,y), obj_type, player_id, margin=0, ghost_margin=0)
                return

            if self._check_placement(points, (x,y), obj_type, margin = 0, width = 1, height = 4):
                obj_type = BuildingInfo[gate_type.value[2]]
                self._place(value_type, (x,y), obj_type, player_id, margin=0, ghost_margin=0)
                return
        return



