from re import I
import numpy as np
from typing import Union, Callable

def generate_city_map(
        size,
        array_space_type_list: Union[int, tuple],
        ):
    
    """
    TODO
    """
    # Initialize the array with zeros.
    array = [[0 for i in range(size)] for j in range(size)]


    
