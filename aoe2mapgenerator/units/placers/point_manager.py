"""
This module contains the PointManager class, which is used to manage points in a set and list.
"""

from typing import Union


# The PointDict maps a point tuple to the index of the point in the list.
PointDict = dict[tuple[int, int], int]


class PointManager:
    """
    Class to manage points in a set and list
    """

    def __init__(self):
        self.points_list = []
        self.points_dict: PointDict = {}

        self.points_removed = 0

    def add_point(self, point: tuple[int, int]) -> None:
        """
        Adds a point to the set and list

        Args:
            point (tuple): The point to add
        """
        if point not in self.points_dict:
            self.points_list.append(point)
            self.points_dict[point] = len(self.points_list) - 1

    def add_points(
        self, points: Union[list[tuple[int, int]], set[tuple[int, int]]]
    ) -> None:
        """
        Adds multiple points to the set and list

        Args:
            points (list): The points to add
        """
        for point in points:
            self.add_point(point)

    def remove_point(self, point: tuple[int, int]) -> None:
        """
        Removes a point from the set and list

        Args:
            point (tuple): The point to remove
        """
        if point in self.points_dict:
            # Get the index of the point to remove
            index = self.points_dict[point]
            # Remove the point from the dictionary
            del self.points_dict[point]

            # If the point is not the last element, swap with the last element
            if index != len(self.points_list) - 1:
                # Get the last point
                last_point = self.points_list[-1]
                # Swap the last point with the point to remove
                self.points_list[index] = last_point
                # Update the dictionary to point to the new index
                self.points_dict[last_point] = index

            # Remove the last element from the list
            self.points_list.pop()

        self.points_removed += 1

    def remove_points(
        self, points: Union[list[tuple[int, int]], set[tuple[int, int]]]
    ) -> None:
        """
        Removes multiple points from the set and list

        Args:
            points (list): The points to remove
        """
        for point in points:
            self.remove_point(point)

    def check_point_exists(self, point: tuple[int, int]) -> bool:
        """
        Checks if a point exists in the set

        Args:
            point (tuple): The point to check
        """
        return point in self.points_dict

    def get_sorted_points(self) -> list[tuple[int, int]]:
        """
        Gets the list of points sorted

        Args:
            point (tuple): The point to check
        """
        return sorted(self.points_list)

    def get_point_dict(self) -> dict[tuple[int, int], int]:
        """
        Gets the dictionary of points

        Args:
            point (tuple): The point to check
        """
        return self.points_dict

    def get_point_list(self) -> list[tuple[int, int]]:
        """
        Gets the list of points

        Returns:
            list: The list of points

        Note:
            This often should not be used since this point list is a reference to a list,
            which means that if we iterate over the points in this list, we will have an issue
            where points are getting removed from the list as we are iterating over it.
            This should only be used in cases where we are not modifying the list.
        """
        return self.points_list

    def get_point_list_copy(self) -> list[tuple[int, int]]:
        """
        Gets the list of points
        """
        return self.points_list.copy()

    def get_nearby_points(
        self, point: tuple[int, int], search_distance: int
    ) -> list[tuple[int, int]]:
        """
        Returns the k nearest points to the given point

        Args:
            point (tuple): The point to find the nearest points to
        """
        return self._get_points_within_distance(point, search_distance)

    def _get_points_within_distance(
        self, point: tuple[int, int], distance: float
    ) -> list[tuple[int, int]]:
        """
        Returns all points within a certain distance of the given point

        Args:
            point (tuple): The point to find the nearest points to
            distance (float): The maximum distance from the point to include
        """
        points = []

        for i in range(-int(distance), int(distance) + 1):
            for j in range(-int(distance), int(distance) + 1):
                if i + j <= distance and self.check_point_exists(
                    (point[0] + i, point[1] + j)
                ):
                    points.append((point[0] + i, point[1] + j))

        return points

    def get_leftmost_point(self) -> tuple[int, int]:
        """
        Gets the leftmost point in the set
        """
        return min(self.points_list, key=lambda point: point[1])

    def get_rightmost_point(self) -> tuple[int, int]:
        """
        Gets the rightmost point in the set
        """
        return max(self.points_list, key=lambda point: point[1])

    def get_topmost_point(self) -> tuple[int, int]:
        """
        Gets the topmost point in the set
        """
        return min(self.points_list, key=lambda point: point[0])

    def get_bottommost_point(self) -> tuple[int, int]:
        """
        Gets the bottommost point in the set
        """
        return max(self.points_list, key=lambda point: point[0])

    def get_theoretical_top_left_corner_point(self) -> tuple[int, int]:
        """
        Gets the theoretical top left corner point in the set
        """
        x = self.get_topmost_point()[0]
        y = self.get_leftmost_point()[1]
        return (x, y)

    def get_maximal_points(
        self,
    ) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
        """
        Gets the maximal points in the set
        """
        return (
            self.get_leftmost_point(),
            self.get_rightmost_point(),
            self.get_topmost_point(),
            self.get_topmost_point(),
        )

    def get_y_point_range(self) -> int:
        """
        Gets the range of x values in the set
        """
        return 1 + abs(self.get_leftmost_point()[1] - self.get_rightmost_point()[1])

    def get_x_point_range(self) -> int:
        """
        Gets the range of y values in the set
        """
        return 1 + abs(self.get_topmost_point()[0] - self.get_bottommost_point()[0])

    def clear(self):
        """
        Clears the point manager
        """
        self.points_list = []
        self.points_dict = {}
        self.points_removed = 0
