"""
This module contains the PointCollection class, which is used to store points in a set and list.
"""

from typing import Union, List, Dict, Tuple
from src.units.placers.point_management.points_returned import PointPlacementResults

# The Point type is a tuple of two integers.
Point = Tuple[int, int]
# The PointDict maps a point tuple to the index of the point in the list.
PointDict = Dict[Point, int]


class PointCollection:
    """
    This is a class to store points in a set and list.
    """

    def __init__(self) -> None:
        self.__points_list: List[Point] = []
        self.__points_dict: PointDict = {}
        self.points_removed: int = 0
        self.name: str = ""

    def add_point(self, point: Point) -> None:
        """
        Adds a point to the set and list

        Args:
            point (tuple): The point to add
        """
        if point not in self.__points_dict:
            self.__points_list.append(point)
            self.__points_dict[point] = len(self.__points_list) - 1

    def add_points(self, points: Union[List[Point], set[Point]]) -> None:
        """
        Adds multiple points to the set and list

        Args:
            points (list): The points to add
        """
        for point in points:
            self.add_point(point)

    def remove_point(self, point: Point) -> None:
        """
        Removes a point from the set and list

        Args:
            point (tuple): The point to remove
        """
        if point in self.__points_dict:
            # Get the index of the point to remove
            index = self.__points_dict[point]
            # Remove the point from the dictionary
            del self.__points_dict[point]

            # If the point is not the last element, swap with the last element
            if index != len(self.__points_list) - 1:
                # Get the last point
                last_point = self.__points_list[-1]
                # Swap the last point with the point to remove
                self.__points_list[index] = last_point
                # Update the dictionary to point to the new index
                self.__points_dict[last_point] = index

            # Remove the last element from the list
            self.__points_list.pop()

        self.points_removed += 1

    def remove_points(self, points: Union[List[Point], set[Point]]) -> None:
        """
        Removes multiple points from the set and list

        Args:
            points (list): The points to remove
        """
        for point in points:
            self.remove_point(point)

    def clear_points(self) -> None:
        """
        Clears the points in the set and list
        """
        self.__points_list = []
        self.__points_dict = {}

    def intersect(
        self, other: "PointCollection", edit_in_place: bool = False
    ) -> "PointCollection":
        """
        Returns a new PointCollection with the intersection of this and another PointCollection

        Args:
            other (PointCollection): The other PointCollection to intersect with
        """
        if edit_in_place:
            points_copy = self.get_point_list_copy()

            for point in points_copy:
                if point not in other.get_point_list():
                    self.remove_point(point)
            return self

        new_point_collector = PointCollection()
        new_point_collector.add_points(
            set(self.get_point_list()).intersection(set(other.get_point_list()))
        )
        return new_point_collector

    def check_point_exists(self, point: Point) -> bool:
        """
        Checks if a point exists in the set

        Args:
            point (tuple): The point to check
        """
        return point in self.__points_dict

    def get_point_dict(self) -> PointDict:
        """
        Gets the dictionary of points

        Args:
            point (tuple): The point to check
        """
        return self.__points_dict

    def get_point_list(self) -> List[Point]:
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
        return self.__points_list

    def get_point_list_copy(self) -> List[Point]:
        """
        Gets the list of points
        """
        return self.__points_list.copy()

    def get_nearby_points(self, point: Point, search_distance: int) -> List[Point]:
        """
        Returns the k nearest points to the given point

        Args:
            point (tuple): The point to find the nearest points to
        """
        return self._get_points_within_distance(point, search_distance)

    def _get_points_within_distance(self, point: Point, distance: float) -> List[Point]:
        """
        Returns all points within a certain distance of the given point

        Args:
            point (tuple): The point to find the nearest points to
            distance (float): The maximum distance from the point to include
        """
        points: List[Point] = []

        for i in range(-int(distance), int(distance) + 1):
            for j in range(-int(distance), int(distance) + 1):
                if i + j <= distance and self.check_point_exists(
                    (point[0] + i, point[1] + j)
                ):
                    points.append((point[0] + i, point[1] + j))

        return points

    def get_leftmost_point(self) -> Point:
        """
        Gets the leftmost point in the set
        """
        return min(self.__points_list, key=lambda point: point[1])

    def get_rightmost_point(self) -> Point:
        """
        Gets the rightmost point in the set
        """
        return max(self.__points_list, key=lambda point: point[1])

    def get_topmost_point(self) -> Point:
        """
        Gets the topmost point in the set
        """
        return min(self.__points_list, key=lambda point: point[0])

    def get_bottommost_point(self) -> Point:
        """
        Gets the bottommost point in the set
        """
        return max(self.__points_list, key=lambda point: point[0])

    def get_theoretical_top_left_corner_point(self) -> Point:
        """
        Gets the theoretical top left corner point in the set
        """
        x = self.get_topmost_point()[0]
        y = self.get_leftmost_point()[1]
        return (x, y)

    def get_theoretical_bottom_right_corner_point(self) -> Point:
        """
        Gets the theoretical bottom right corner point in the set
        """
        x = self.get_bottommost_point()[0]
        y = self.get_rightmost_point()[1]
        return (x, y)

    def get_theoretical_top_right_corner_point(self) -> Point:
        """
        Gets the theoretical top right corner point in the set
        """
        x = self.get_topmost_point()[0]
        y = self.get_rightmost_point()[1]
        return (x, y)

    def get_theoretical_bottom_left_corner_point(self) -> Point:
        """
        Gets the theoretical bottom left corner point in the set
        """
        x = self.get_bottommost_point()[0]
        y = self.get_leftmost_point()[1]
        return (x, y)

    def get_maximal_points(
        self,
    ) -> Tuple[Point, Point, Point, Point]:
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

    def get_neighbors(self, point: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Gets the neighbors of a point

        Args:
            point (tuple[int, int]): The point to get the neighbors of
        """
        x, y = point

        neighbors = [
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ]

        return [neighbor for neighbor in neighbors if self.check_point_exists(neighbor)]

    def clear(self) -> None:
        """
        Clears the point collector
        """
        self.__points_list = []
        self.__points_dict = {}
        self.points_removed = 0

    def copy(self) -> "PointCollection":
        """
        Copies the point collector
        """
        new_point_collector = PointCollection()
        new_point_collector.add_points(self.get_point_list())
        return new_point_collector
    
    def filter_by_distance(
        self, reference_point: Point, distance: float, edit_in_place: bool = False
    ) -> "PointCollection":
        """
        Filters the points to only include those within the specified distance of the reference point.

        Args:
            reference_point (Point): The reference point to measure distance from
            distance (float): The maximum distance from the reference point to include
            edit_in_place (bool, optional): Whether to modify this collection in place. Defaults to False.

        Returns:
            PointCollection: A new collection with the filtered points, or this collection if edit_in_place is True
        """
        points_within_distance = self._get_points_within_distance(reference_point, distance)
        
        if edit_in_place:
            points_copy = self.get_point_list_copy()
            for point in points_copy:
                if point not in points_within_distance:
                    self.remove_point(point)
            return self
        else:
            new_collection = PointCollection()
            new_collection.add_points(points_within_distance)
            return new_collection
