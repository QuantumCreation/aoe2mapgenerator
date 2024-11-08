"""
This module contains the PointManager class, which is used to manage points in a set and list.
"""

from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.units.placers.point_management.point_selector import (
    PointSelector,
)
from aoe2mapgenerator.src.units.placers.point_management.point_collection import (
    PointCollection,
)

# The Point type is a tuple of two integers.
Point = tuple[int, int]
# The PointDict maps a point tuple to the index of the point in the list.
PointDict = dict[Point, int]


class PointManager:
    """
    Class to manage points in a dict and list
    """

    def __init__(self, aoe2map: Map):

        self.map: Map = aoe2map
        self.point_selector = PointSelector(self.map)

        self.__point_collections: dict[str, PointCollection] = {}
        self.points_removed: int = 0

    def add_point_collection(self, name: str, points: list[Point] = []) -> None:
        """
        Adds a point collection to the list

        Args:
            name (str): The name of the point collection
            points (list[Point]): The list of points to add to the collection
        """
        if name in self.__point_collections:
            raise ValueError(
                f"A point collection with the name '{name}' already exists."
            )

        point_collection = PointCollection()
        point_collection.add_points(points)

        self.__point_collections[name] = point_collection

    def get_point_collection(self, name: str) -> PointCollection:
        """
        Gets a point collection from the list

        Args:
            name (str): The name of the point collection
        """
        if name not in self.__point_collections:
            raise ValueError(
                f"A point collection with the name '{name}' does not exist."
            )
        return self.__point_collections[name]

    def list_point_collections(self) -> list[str]:
        """
        Lists all the point collections
        """
        return list(self.__point_collections.keys())
