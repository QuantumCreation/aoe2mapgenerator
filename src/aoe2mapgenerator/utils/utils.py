"""
Contains utility functions for all classes
"""

import inspect


def set_from_matrix(matrix):
    """
    Takes a matrix and gets a set of the values.

    Args:
        matrix: Matrix to flatten.
    """
    result = set()

    for row in matrix:
        for ele in row:
            result.add(ele)

    return result


def unique_value_list(matrix):
    """
    Takes a matrix and returns a list of the unique values.

    Args:
        matrix: Matrix to get unique values from.
    """
    return list(set_from_matrix(matrix))


def current_function_name():
    """
    Returns the name of the current function.
    """
    return inspect.stack()[2].function


def combine_test_name_and_function_name(test_name: str):
    """
    Combines the test name with the function name.
    """
    return test_name + "|" + current_function_name()
