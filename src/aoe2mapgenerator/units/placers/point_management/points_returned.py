from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.common.types import Point


class PointPlacementResults:

    def __init__(self) -> None:
        """
        Pass
        """
        self.object_dict: dict[MapObject, set[Point]] = {}

    def add_object(self, point: tuple, map_object: MapObject) -> None:
        """
        Adds a placed object to the results.

        Args:
            point (tuple): Point where the object was placed.
            object_type (MapObject): Map object
        """
        if map_object not in self.object_dict:
            self.object_dict[map_object] = set()

        self.object_dict[map_object].add(point)

    def add_objects(self, points: list[tuple], object_type: MapObject) -> None:
        """
        Adds multiple placed objects to the results.

        Args:
            points (list[tuple]): Points where the objects were placed.
            object_type (MapObject): Type of object placed.
        """
        for point in points:
            self.add_object(point, object_type)

    def remove_object(self, point: tuple, object_type: MapObject) -> None:
        """
        Removes a placed object from the results.

        Args:
            point (tuple): Point where the object was placed.
            object_type (MapObject): Type of object placed.
        """
        if object_type in self.object_dict:

            if point in self.object_dict[object_type]:
                self.object_dict[object_type].remove(point)
                if not self.object_dict[object_type]:
                    del self.object_dict[object_type]

    def remove_objects(self, points: list[tuple], object_type: MapObject) -> None:
        """
        Removes multiple placed objects from the results.

        Args:
            points (list[tuple]): Points where the objects were placed.
            object_type (MapObject): Type of object placed.
        """
        for point in points:
            self.remove_object(point, object_type)

    def combine_results(self, other_results: "PointPlacementResults") -> None:
        """
        Combines the results of another PointPlacementResults object.

        Args:
            other_results (PointPlacementResults): Other results to combine.
        """
        for object_type, points in other_results.object_dict.items():
            if object_type not in self.object_dict:
                self.object_dict[object_type] = set()
            self.object_dict[object_type].update(points)

    def clear_objects(self) -> None:
        """
        Clears all placed objects from the results.
        """
        self.object_dict.clear()

    def get_objects(self, object_type: MapObject) -> set[Point]:
        """
        Gets all placed objects of a specific type.

        Args:
            object_type (MapObject): Type of object to get.

        Returns:
            set[tuple]: Set of points where the objects were placed.
        """
        return self.object_dict.get(object_type, set())
