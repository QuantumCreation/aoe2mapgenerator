from typing import Union, Callable

class PointManager():
    """
    Class to manage points in a set and list
    """

    def __init__(self):
        self.points_list = []
        self.points_dict = {}

        self.points_removed = 0
    
    def add_point(self, point: tuple[float, float]) -> None:
        if point not in self.points_dict:
            self.points_list.append(point)
            self.points_dict[point] = len(self.points_list) - 1
    
    def add_points(self, points: Union[list[tuple[float,float]], set[tuple[float,float]]]) -> None:
        for point in points:
            self.add_point(point)

    def remove_point(self, point: tuple[float, float]) -> None:
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

    def remove_points(self, points: Union[list[tuple[float,float]], set[tuple[float,float]]]) -> None:
        for point in points:
            self.remove_point(point)

    def check_point_exists(self, point: tuple[float, float]) -> bool:
        return point in self.points_dict

    def get_sorted_points(self) -> list:
        return sorted(self.points_list)
    
    def get_point_set(self) -> set:
        return self.points_dict
    
    def get_point_list(self) -> list:
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
    
    def get_point_list_copy(self) -> list:
        return self.points_list.copy()
    
    def get_nearby_points(self, point: tuple[float, float], search_distance: int) -> list:
        """
        Returns the k nearest points to the given point
        
        Args:
            point (tuple): The point to find the nearest points to
        """
        return self._get_points_within_distance(point, search_distance)
    
    def _get_points_within_distance(self, point: tuple[float, float], distance: float) -> list:
        """
        Returns all points within a certain distance of the given point
        
        Args:
            point (tuple): The point to find the nearest points to
            distance (float): The maximum distance from the point to include
        """
        points = []

        for i in range(-int(distance), int(distance) + 1):
            for j in range(-int(distance), int(distance) + 1):
                if i + j <= distance and self.check_point_exists((point[0] + i, point[1] + j)):
                    points.append((point[0] + i, point[1] + j))

        return points

