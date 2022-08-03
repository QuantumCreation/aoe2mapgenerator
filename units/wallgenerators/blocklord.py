
import random

def blocklord(map,x,y,size,blockiness):
    """
    TODO
    """

def r(start, end):
    """
    TODO
    """
    return random.random()*(end-start)+start

def start(x, y, size):
    """
    TODO
    """
    points = [
        [x,y],
        [x,y+size-1],
        [x+size-1,y+size-1],
        [x+size-1,y],
    ]

    return points


def grow(array, blockiness):
    """
    TODO
    """

    start_index = r(0, len(array)-1)
    (x1, y1) = array[start_index]
    (x2, y2) = array[(start_index+1)%len(array)]

    if y2-y1 > 0:
        new_point_one = [r(x1,x1-10), r(y1, (y2-y1)//2)]
        new_point_two = [new_point_one[0], r(new_point_one[1], y2)]
    elif x2-x1 > 0:
        new_point_one = [r(x1,x1-10), r(y1, (y2-y1)//2)]
        new_point_two = [new_point_one[0], r(new_point_one[1], y2)]
    elif y2-y1 < 0:
    elif x2-x1 < 0:
        ***************************** WIP
