
import random
from re import A
from constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPE


def check_placement(obj_space, point, obj_size, margin, width = -1, height = -1):
    """
    Checks if the given point is a valid placement for an object.

    Args:
        obj_space: Set containing all possible points within a cell.
        point: X and y coordinates for where the object is attempting to be placed.
        obj_size: square size of the object.
        margin: Margin between object placements.
        width: TBD
        height: TBD
    """
    eff_size = obj_size + margin

    x, y = point

    for i in range(-margin, eff_size):
        for j in range(-margin, eff_size):
            if (x+i,y+j) not in obj_space:
                return False
    
    return True

def place(map, point, obj_type, obj_size, margin):
    """
    Places a single object. Assumes placement has already been verified.

    Args:
        map: Map object with the corresponding array and set of points.
        point: Point to place base of object.
        obj_type: The type of object to be placed.
        obj_size: Size of object to be placed.
        margin: Area around the object to be placed.
    """
    eff_size = obj_size + margin
    x, y = point

    for i in range(-margin, eff_size):
        for j in range(-margin, eff_size):
            map.set_point(x+i,y+j,GHOST_OBJECT_DISPLACEMENT)
    
    map.set_point(x+obj_size//2, y+obj_size//2, obj_type)

    return


"""
DEPRECATED
"""
def get_valid_points(array, array_space_type):
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
            
def place_one(map, array_space_type, obj_type, obj_size, margin):
    """
    Finds an open space and then places an object.

    Args:
        map: Map object with the corresponding array and set of points.
        array_space_type: Array space id to get points for.
        obj_type: The type of object to be placed.
        obj_size: Size of object to be placed.
        margin: Area around the object to be placed.
    """
    
    if array_space_type in map.object_dict:
        points = map.object_dict[array_space_type]
    else:
        return
    


    for (x,y) in sorted(points, key = lambda _: random.random()):
        if check_placement(points, (x,y), obj_size=obj_size, margin=margin):
            place(map, (x,y), obj_type=obj_type, obj_size=obj_size, margin=margin)
            return True
    
    return False
    

def place_group(map, array_space_type, obj_type, obj_size, margin = 0, group_size = 1, clumping = 1):
    """
    TODO
    """
    if array_space_type in map.object_dict:
        points = map.object_dict[array_space_type]
    else:
        return

    points_list = list(points)
    (xrand, yrand) = points_list[int(random.random()*len(points))]

    placed = 0
    for (x,y) in sorted(points_list, key = lambda a: ((a[0]-xrand)**2 + (a[1]-yrand)**2 + random.random()*((clumping)**2))):

        if placed >= group_size:
            return

        if check_placement(points, (x,y), obj_size=obj_size, margin=margin):
            place(map, (x,y), obj_type=obj_type, obj_size=obj_size, margin=margin)
            placed += 1

    return

def place_groups(map, array_space_type, obj_type, obj_size, margin = 0, group_size = 1, groups = 1, clumping = 1):
    """
    TODO
    """
    for i in range(groups):
        place_group(map, array_space_type, obj_type, obj_size, margin, group_size, clumping)

def place_all(map, array_space_type, obj_type = DEFAULT_OBJECT_TYPE, obj_size = 1,  margin = 0, total = 1):
    """
    Places n number of objects randomly.

    Args:
        map: Map object with the corresponding array and set of points.
        array_space_type: Array space id to get points for.
        obj_type: The type of object to be placed.
        obj_size: Size of object to be placed.
        margin: Area around the object to be placed.
        total: Total number of objects to place.
    """

    for i in range(total):
        if not place_one(map, array_space_type=array_space_type, obj_type=obj_type, obj_size=obj_size, margin=margin):
            return
    
    return

def distance_to_edge(points, point):
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

def is_on_border(points, point, border_margin):
    """
    Checks if given point is on a border

    Args:
        points: Set of all points in space.
        point: single point to find distance for.
    """
    x, y = point

    for dist in range(1,border_margin+1):
        for i in range(-dist,dist+1):
            for j in range(-dist,dist+1):
                if not (x+i,y+j) in points:
                    return True

    return False

def add_borders(map, array_space_type, border_type = 1, border_margin = 1):
    """
    Adds borders to a cell based on border margin size and type.

    Args:
        array: Array of the complete map space.
        array_space_type: Array space id to get points for.
        border_type: Type of border to place.
        border_margin: Type of margin to place.
    """
    if array_space_type in map.object_dict:
        points = map.object_dict[array_space_type].copy()
    else:
        return

    for point in points:
        if is_on_border(points, point, border_margin):
            x, y = point
            map.set_point(x,y,border_type)
    
    return
