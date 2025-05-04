"""
This module contains the PointManager class, which is used to manage points in a set and list.
"""

from src.map.map import Map
from src.units.placers.point_management.point_selector import (
    PointSelector,
    PointSelectorConfig,
)
from src.units.placers.point_management.point_collection import (
    PointCollection,
)
from src.common.enums.enum import MapLayerType
from AoE2ScenarioParser.datasets.terrains import TerrainId
from typing import Tuple, Union, Callable, Optional, List, Dict, TypeVar, Any, cast
import random

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

    def add_point_collection(
        self, name: str, points: list[Point] = [], make_unique=False
    ) -> PointCollection:
        """
        Adds a point collection to the list

        Args:
            name (str): The name of the point collection
            points (list[Point]): The list of points to add to the collection

        Returns: Name of the point collection
        """
        if make_unique:
            name = self.__make_unique_name(name)

        if name in self.__point_collections:
            raise ValueError(
                f"A point collection with the name '{name}' already exists."
            )

        point_collection = PointCollection()
        point_collection.add_points(points)

        point_collection.name = name
        self.__point_collections[name] = point_collection

        return point_collection

    def remove_point_collection(self, name: str) -> None:
        """
        Removes a point collection from the list

        Args:
            name (str): The name of the point collection
        """
        if name not in self.__point_collections:
            raise ValueError(
                f"A point collection with the name '{name}' does not exist."
            )

        del self.__point_collections[name]

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

    def __make_unique_name(self, name: str) -> str:
        """
        Makes a unique name for the point collection
        """
        i = 1
        new_name = name
        while new_name in self.__point_collections:
            new_name = f"{name}_{i}"
            i += 1
        return new_name

    def create_point_collection(self, name: str | None = None, points: list[Point] | None = None) -> PointCollection:
        """
        Creates a new point collection without adding it to the managed collections.
        This is useful for temporary collections or when you want to manage the 
        collection's lifecycle yourself.
        
        Args:
            name (str, optional): Name for the collection
            points (list[Point], optional): Initial points
            
        Returns:
            PointCollection: A new point collection
        """
        collection = PointCollection()
        if name:
            collection.name = name
        if points:
            collection.add_points(points)
        return collection
        
    def merge_collections(self, 
                         collections: list[Union[str, PointCollection]], 
                         result_name: str | None = None,
                         register: bool = False) -> PointCollection:
        """
        Merges multiple point collections into a new one
        
        Args:
            collections: List of collection names or PointCollection objects
            result_name: Optional name for the resulting collection
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: The merged collection
        """
        result = PointCollection()
        if result_name:
            result.name = result_name
            
        for collection in collections:
            if isinstance(collection, str):
                # Get the collection by name if a string is provided
                collection = self.get_point_collection(collection)
            result.add_points(collection.get_point_list_copy())
            
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
        
    def subtract_collections(self, 
                           collection_a: Union[str, PointCollection], 
                           collection_b: Union[str, PointCollection],
                           result_name: str | None = None,
                           register: bool = False) -> PointCollection:
        """
        Returns points that are in collection A but not in collection B
        
        Args:
            collection_a: First collection name or object
            collection_b: Collection to subtract (name or object)
            result_name: Optional name for the resulting collection
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: Result of subtraction operation
        """
        # Convert names to collections if needed
        if isinstance(collection_a, str):
            collection_a = self.get_point_collection(collection_a)
        if isinstance(collection_b, str):
            collection_b = self.get_point_collection(collection_b)
            
        result = PointCollection()
        if result_name:
            result.name = result_name
            
        for point in collection_a.get_point_list_copy():
            if not collection_b.check_point_exists(point):
                result.add_point(point)
                
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
        
    def filter_collection(self, 
                         collection: Union[str, PointCollection],
                         filter_func: Callable[[Point], bool],
                         result_name: str | None = None,
                         register: bool = False) -> PointCollection:
        """
        Filters a collection using a custom function
        
        Args:
            collection: Collection name or object to filter
            filter_func: Function that takes a point and returns True to keep it
            result_name: Optional name for the resulting collection
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: Filtered collection
        """
        # Convert name to collection if needed
        if isinstance(collection, str):
            collection = self.get_point_collection(collection)
            
        result = PointCollection()
        if result_name:
            result.name = result_name
            
        for point in collection.get_point_list_copy():
            if filter_func(point):
                result.add_point(point)
                
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
    
    def get_points_in_radius(self, 
                           center: Point, 
                           radius: float,
                           source_collection: Union[str, PointCollection] | None = None,
                           result_name: str | None = None,
                           register: bool = False) -> PointCollection:
        """
        Gets all points within a radius of a center point
        
        Args:
            center: Center point (x, y)
            radius: Radius to select points within
            source_collection: Optional source collection (if None, considers valid map points)
            result_name: Optional name for the resulting collection
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: Points within the specified radius
        """
        result = PointCollection()
        if result_name:
            result.name = result_name
        
        # If source collection is provided
        if source_collection:
            if isinstance(source_collection, str):
                source_collection = self.get_point_collection(source_collection)
                
            for point in source_collection.get_point_list_copy():
                distance = ((center[0] - point[0])**2 + (center[1] - point[1])**2)**0.5
                if distance <= radius:
                    result.add_point(point)
        else:
            # Create points for the entire map area
            for x in range(self.map.size):
                for y in range(self.map.size):
                    distance = ((center[0] - x)**2 + (center[1] - y)**2)**0.5
                    if distance <= radius:
                        result.add_point((x, y))
                        
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
        
    def get_random_points(self,
                        collection: Union[str, PointCollection],
                        count: int = 1,
                        result_name: str | None = None,
                        register: bool = False) -> PointCollection:
        """
        Randomly selects points from a collection
        
        Args:
            collection: Collection name or object to select from
            count: Number of points to select
            result_name: Optional name for the resulting collection
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: Collection with randomly selected points
        """
        # Convert name to collection if needed
        if isinstance(collection, str):
            collection = self.get_point_collection(collection)
            
        points = collection.get_point_list_copy()
        result = PointCollection()
        if result_name:
            result.name = result_name
            
        if points:
            selected = random.sample(points, min(count, len(points)))
            result.add_points(selected)
            
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
        
    def get_border_points(self,
                        collection: Union[str, PointCollection],
                        result_name: str | None = None,
                        register: bool = False) -> PointCollection:
        """
        Gets points on the border of a collection (points with at least one
        non-collection neighbor)
        
        Args:
            collection: Collection name or object to find borders of
            result_name: Optional name for the resulting collection
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: Collection of border points
        """
        # Convert name to collection if needed
        if isinstance(collection, str):
            collection = self.get_point_collection(collection)
            
        result = PointCollection()
        if result_name:
            result.name = result_name
            
        for point in collection.get_point_list_copy():
            x, y = point
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            
            # If any neighbor is not in the collection, this is a border point
            for neighbor in neighbors:
                if not collection.check_point_exists(neighbor):
                    result.add_point(point)
                    break
                    
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
        
    def get_collection_from_terrain(self,
                                  terrain_type: TerrainId,
                                  result_name: str | None = None,
                                  limit: int | None = None,
                                  exclude_occupied: bool = True,
                                  register: bool = False) -> PointCollection:
        """
        Creates a point collection from terrain points
        
        Args:
            terrain_type: Terrain type to find
            result_name: Optional name for the resulting collection
            limit: Maximum number of points to include (None for all)
            exclude_occupied: Whether to exclude points with objects
            register: Whether to register the new collection in the manager
            
        Returns:
            PointCollection: Collection with points of the specified terrain
        """
        config = PointSelectorConfig(
            map_layer_type=MapLayerType.TERRAIN,
            object_type=terrain_type
        )
        
        points = self.point_selector.get_points_from_map_layer(config)
        
        # If exclude_occupied is True, filter out points that have units
        if exclude_occupied:
            points = [
                point for point in points 
                if not self.map.get_map_layer(MapLayerType.UNIT).get_object_at_point(point)
            ]
        
        if limit and len(points) > limit:
            points = random.sample(points, limit)
            
        result = PointCollection()
        if result_name:
            result.name = result_name
            
        result.add_points(points)
        
        if register and result_name:
            self.__point_collections[result_name] = result
            
        return result
