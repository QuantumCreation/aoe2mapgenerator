import numpy as np
from matplotlib.pylab import matshow
import matplotlib.pyplot as plt


def connect(ends):
    """
    Connects a start and end point.

    Args:
        ends: List with a start (x,y) coordinate and an end (x,y) coordinate.
    """
    d0, d1 = np.abs(np.diff(ends, axis=0))[0]
    if d0 > d1: 
        return np.c_[np.linspace(ends[0, 0], ends[1, 0], d0+1, dtype=np.int32),
                     np.round(np.linspace(ends[0, 1], ends[1, 1], d0+1))
                     .astype(np.int32)]
    else:
        return np.c_[np.round(np.linspace(ends[0, 0], ends[1, 0], d1+1))
                     .astype(np.int32),
                     np.linspace(ends[0, 1], ends[1, 1], d1+1, dtype=np.int32)]


def connect_points(point_list):
    """
    Creates list of all connecting points for a list of outer perimeter points.

    Args:
        point_list: list of outer perimeter points in order
    
    Returns list of points connecting each adjacent set of perimeter points
    """
    returned_points = []

    for i, (x, y) in enumerate(point_list):
        next_point = [point_list[(i+1)%len(point_list)][0],point_list[(i+1)%len(point_list)][1]]
        new_points = connect(np.array([[x,y], next_point]))
        returned_points.extend(new_points)  

    return returned_points

def generate_polygonal_wall_points(x,y,corner_points, radius):
    """
    Generates sequential points forming the outer perimeter of a wall.

    Args:
        x: x coordinate to center the wall.
        y: y coordinate to center the wall.
        corner_points: Number of corner pointers to create.
        radius: radius of the walls.
    
    Returns points to define the outer perimeter.
    """
    points = []
    angles = np.array(list(range(corner_points)))*(2*np.pi)/corner_points
    
    for i, angle in enumerate(angles):
        px = np.cos(angle)*radius
        py = np.sin(angle)*radius
        px = int(px)
        py = int(py)
        points.append([x+px, y+py])
    
    return points

def generate_polygonal_wall(x, y, corner_points, radius):
    """
    Generatres a polygonal wall centered around the x and y coordinates.

    Args:
        x: x coordinate center.
        y: y coordinate center.
        corner_points: Number of corners for polygon.
        radius: Radius of the polygon.
    """
    points = generate_polygonal_wall_points(x, y, corner_points, radius)
    points = connect_points(points)

    return np.array(points)

    
def generate_poisson_voronoi_point_distribution(size, interpoint_distance):
    """
    Generates a list of points for creating a voronoi pattern
    """
    k = 40

    points = poisson_disk_sample(size,size,interpoint_distance,k)
    points = np.ndarray.tolist(points)

    for i, (a,b) in enumerate(points):
        points[i] = [int(a), int(b)]
    
    return points


def valid(array, x, y):
    """
    Checks that point coordinates are valid
    """
    return (0<=x<len(array)) and (0<=y<len(array[0]))
