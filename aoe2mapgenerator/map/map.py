from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable
import numpy as np

from aoe2mapgenerator.common.constants.constants import DEFAULT_EMPTY_VALUE, DEFAULT_OBJECT_AND_PLAYER
from aoe2mapgenerator.units.wallgenerators.voronoi import VoronoiGeneratorMixin
from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.objectplacer import PlacerMixin
from aoe2mapgenerator.units.placers.templateplacer import TemplatePlacerMixin
from aoe2mapgenerator.map.map_utils import MapUtilsMixin
from aoe2mapgenerator.visualizer.visualizer import VisualizerMixin

class Map(TemplatePlacerMixin, VisualizerMixin, VoronoiGeneratorMixin, MapUtilsMixin):
    """
    TODO
    """

    def __init__(self, size: int = 100):
        """
        Initializes map object for internal map representation.

        Args:
            size: Size of the map.
        """
        # TEMPLATE NAMES, MULTIPLE INHERITANCE, init, AAHGHG
        self.template_names = {}
        self.size = size

        self.unit_map_layer = MapLayer(MapLayerType.UNIT, self.size)
        self.zone_map_layer = MapLayer(MapLayerType.ZONE, self.size)
        self.terrain_map_layer = MapLayer(MapLayerType.TERRAIN, self.size)
        self.decor_map_layer = MapLayer(MapLayerType.DECOR, self.size)
        self.elevation_map_layer = MapLayer(MapLayerType.ELEVATION, self.size)

        self.world_partition = WorldPartition(self.size, partition_size=10)

    def get_world_partition(self, start_point, points_needed, clumping = 1):
        return self.world_partition.get_world_partition(start_point, points_needed, clumping)

    def get_map_layer(self, map_layer_type: MapLayerType):
        """
        Gets the corresponding map layer from a map layer type.
        """
        var = MapLayerType.UNIT

        if not isinstance(map_layer_type, MapLayerType):
            raise ValueError("Map layer type is not a MapLayerType.")
        
        if map_layer_type == MapLayerType.ZONE:
            return self.zone_map_layer
        elif map_layer_type == MapLayerType.TERRAIN:
            return self.terrain_map_layer
        elif map_layer_type == MapLayerType.UNIT:
            return self.unit_map_layer
        elif map_layer_type == MapLayerType.DECOR:
            return self.decor_map_layer
        elif map_layer_type == MapLayerType.ELEVATION:
            return self.elevation_map_layer
        
        raise ValueError("Retrieving map layer from map layer type failed.")

    def set_point(self, x, y, new_value, map_layer_type: Union[MapLayerType, int], player_id : PlayerId = PlayerId.GAIA):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        layer = self.get_map_layer(map_layer_type)
        layer.set_point(x, y, new_value, player_id)

    # THIS PROBOBLY BELONGS SOMEWHERE ELSE, Also handle defaults better somehow
    def voronoi(self, 
                interpoint_distance: int = 25,
                map_layer_type_list: list = 
                [may_layer_type for may_layer_type in MapLayerType],
                array_space_type_list: list = 
                [DEFAULT_OBJECT_AND_PLAYER for i in range(5)]
                ) -> list:
        """
        Generates a voronoi cell map.

        Args:
            interpoint_distance (int): Minimum distance between points.
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.
        
        Returns:
            list: List of unqiue values for each voronoi cell.
        """
        # Generate voronoi cells. Implicitly edits the map.
        voronoi_zones = self.generate_voronoi_cells(
                                    interpoint_distance,
                                    map_layer_type_list,
                                    array_space_type_list)

        return voronoi_zones       

class MapLayer():
    """
    Single Map type constructor.
    """

    def __init__(self, layer: MapLayerType, size: int = 100, array = [], dictionary = {}):
        
        self.layer = layer
        self.size = size

        if array == []:
            self.array = [[(DEFAULT_EMPTY_VALUE, PlayerId.GAIA) for i in range(size)] for j in range(size)]
        else:
            self.array = array
        
        if dictionary == {}:
            self.dict = _create_dict(self.array)
        else:
            self.dict = dictionary
        
    
    def set_point(self, x, y, new_value, player_id : PlayerId = PlayerId.GAIA):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        # Retrieve correct dictionary and array.
        d = self.dict
        a = self.array
        
        # Remove element from the dictionary.
        d[a[x][y]].remove((x,y))

        # Remove entire dictionary entry if there are not elements left.
        if len(d[a[x][y]]) == 0:
            d.pop(a[x][y], None)

        # Assign new value to the array.
        a[x][y] = (new_value, player_id)

        # Add the value to the dictionary.
        if (new_value, player_id) in d:
            d[a[x][y]].add((x,y))
        else:
            d[a[x][y]] = {(x,y)}

class WorldPartition():
    """
    Class for the world partition of the map.

    Info:
        A world partition is a partition of the map into squares in order to speed up the search for points.
    """

    def __init__(self, size: int = 100, partition_size: int = 10):
        """
        Initializes the world partition.

        Args:
            size: Size of the map.
            partition_size: Size of the partitions.
        """

        self.size = size
        self.partition_size = partition_size
        self.world_partition = self.create_world_partition()

    def get_world_partition(self, start_point, points_needed, clumping = 1):
        """
        Gets the world partition of the map.

        Args:
            start_point: Starting point of the world partition.
            points_needed: Number of points needed to be found for the world partition.
            clumping: Clumping of the world partition.
        """
        # v1 = np.log(points_needed)
        # v2 = np.log(self.partition_size)
        
        # distance = int(v1/v2)

        distance = int((((points_needed/100)**(1/2) + 1) // 2) + 1)
        distance = min(distance, self.size//self.partition_size)
        distance += clumping//10
        
        # Gets the sets of points within the distance square of the start point
        sets = [self.world_partition[
                                    (start_point[0]//self.partition_size+i,
                                       start_point[1]//self.partition_size+j)
                                       ] 
                            for i in range(-distance, distance+1) 
                            for j in range(-distance, distance+1)
                            if (start_point[0]//self.partition_size+i,
                                start_point[1]//self.partition_size+j) in self.world_partition
                ]
    
        return sets
    
    def create_world_partition(self):
        """
        Creates the world partition of the map.
        
        Args:
            start_point: Starting point of the world partition.
            points_needed: Number of points needed to be found for the world partition.
        """

        rows = self.size // self.partition_size
        cols = self.size // self.partition_size

        partition = dict()

        for i in range(self.size):
            for j in range(self.size):
                if (i//self.partition_size, j//self.partition_size) in partition:
                    partition[(i//self.partition_size, j//self.partition_size)].add((i,j))
                else:
                    partition[(i//self.partition_size, j//self.partition_size)] = {(i,j)}
        
        return partition
        
def _create_dict(array: list[list[object]]):
    """
    Creates a set representation from the array.
    """

    new_dict = dict()

    for i in range(len(array)):
        for j in range(len(array[0])):
            if array[i][j] in new_dict:
                new_dict[array[i][j]].add((i,j))
            else:
                new_dict[array[i][j]] = {(i,j)}
    
    return new_dict