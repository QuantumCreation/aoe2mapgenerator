
import random
from re import A
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPE, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from map.map_utils import MapUtilsMixin
from utils.utils import set_from_matrix
from common.enums.enum import ObjectSize
from AoE2ScenarioParser.datasets.players import PlayerId

class PlacerMixin(MapUtilsMixin):
    """
    TODO
    """

    def place_all(self, value_type, array_space_type, obj_type = DEFAULT_OBJECT_TYPE, player_id = DEFAULT_PLAYER, margin = 0, total = 1):
        """
        Places n number of objects randomly.

        Args:
            map: Map object with the corresponding array and set of points.
            array_space_type: Array space id to get points for.
            obj_type: The type of object to be placed.
            margin: Area around the object to be placed.
            total: Total number of objects to place.
        """

        for i in range(total):
            if not self._check_and_place(value_type, array_space_type, obj_type, player_id, margin):
                return
        
        return

    def place_group(self, value_type, array_space_type, obj_type = DEFAULT_OBJECT_TYPE, player_id = DEFAULT_PLAYER, margin = 0, group_size = 1, clumping = 1):
        """
        TODO
        """
        dictionary = self.get_dictionary_from_value_type(value_type)

        if array_space_type in dictionary:
            points = dictionary[array_space_type]
        else:
            return 

        points_list = list(points)
        (xrand, yrand) = points_list[int(random.random()*len(points))]

        placed = 0
        for (x,y) in sorted(points_list, key = lambda a: ((a[0]-xrand)**2 + (a[1]-yrand)**2 + random.random()*((clumping)**2))):

            if placed >= group_size:
                return

            if self._check_placement(points, (x,y), obj_type, margin=margin):
                self._place(value_type, (x,y), obj_type, player_id, margin)
                placed += 1

        return

    def place_groups(self, value_type, array_space_type, obj_type = DEFAULT_OBJECT_TYPE, player_id = DEFAULT_PLAYER, margin = 0, group_size = 1, groups = 1, clumping = 1):
        """
        TODO
        """
        for i in range(groups):
            self.place_group(value_type, array_space_type, obj_type, player_id, margin, group_size, clumping)

    def add_borders(self, value_type, array_space_type, border_type, border_margin, player_id = DEFAULT_PLAYER):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            array: Array of the complete map space.
            array_space_type: Array space id to get points for.
            border_type: Type of border to place.
            border_margin: Type of margin to place.
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
    
    # SOMETHING LEADS TO MASSIVE PROBLEMS HERE
    def add_borders_all(self, value_type, border_type, border_margin, player_id = DEFAULT_PLAYER):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            array: Array of the complete map space.
            array_space_type: Array space id to get points for.
            border_type: Type of border to place.
            border_margin: Type of margin to place.
        """
        all_array_space_types = list(set_from_matrix(self.get_array_from_value_type(value_type)))

        for space_type in all_array_space_types:
            self.add_borders(value_type, space_type, border_type, border_margin, player_id=player_id)
        
        return

    # ----------------------- HELPER METHODS --------------------------

    def _check_placement(self, obj_space, point, obj_type, margin, width = -1, height = -1):
        """
        Checks if the given point is a valid placement for an object.

        Args:
            obj_space: Set containing all possible points within a cell.
            point: X and y coordinates for where the object is attempting to be placed.
            margin: Margin between object placements.
            width: TBD
            height: TBD
        """
        # SOMETHING NEEDS TO BE CHANGED HERE
        obj_size = ObjectSize(obj_type._name_).value
        eff_size = obj_size + margin

        x, y = point

        for i in range(-margin, eff_size):
            for j in range(-margin, eff_size):
                if (x+i,y+j) not in obj_space:
                    return False
        
        return True

    def _place(self, value_type, point, obj_type, player_id, margin):
        """
        Places a single object. Assumes placement has already been verified.

        Args:
            map: Map object with the corresponding array and set of points.
            point: Point to place base of object.
            obj_type: The type of object to be placed.
            margin: Area around the object to be placed.
        """
        obj_size = ObjectSize(obj_type._name_).value
        eff_size = obj_size + margin
        x, y = point

        for i in range(-margin, eff_size):
            for j in range(-margin, eff_size):
                if 0<=i<obj_size and 0<=j<obj_size:
                    self.set_point(x+i,y+j,GHOST_OBJECT_DISPLACEMENT, value_type, player_id)
                else:
                    self.set_point(x+i,y+j,GHOST_OBJECT_MARGIN, value_type, player_id)
        
        self.set_point(x+obj_size//2, y+obj_size//2, obj_type, value_type, player_id)

        return
            
    def _check_and_place(self, value_type, array_space_type, player_id, obj_type, margin):
        """
        Finds an open space and then places an object.

        Args:
            map: Map object with the corresponding array and set of points.
            array_space_type: Array space id to get points for.
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
                self._place(self, value_type, (x,y), player_id, obj_type=obj_type, margin=margin)
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
        """
        x, y = point

        for i in range(-border_margin,border_margin+1):
            for j in range(-(abs(i)-border_margin),(abs(i)-border_margin)+1):
                if abs(i)+abs(j)<border_margin and not (x+i,y+j) in points:
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
        