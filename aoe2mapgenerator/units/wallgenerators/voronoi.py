from re import I
import numpy as np
from typing import Union, Callable
import functools
from AoE2ScenarioParser.datasets.players import PlayerId
import random

from aoe2mapgenerator.map.map_utils import MapUtilsMixin

class VoronoiGeneratorMixin(MapUtilsMixin):
    """
    Class for generating voronoi patterns.
    """
    global_zone_counter = 0

    def generate_voronoi_cells(
            self, 
            interpoint_distance: int,
            map_layer_type_list: list,
            array_space_type_list: list,
            ):
        """
        Generates an array of voronoi shapes, with numbers starting from -1 and going down.

        Args:
            interpoint_distance: Minimum distance between points.
            map_layer_type_list: List of map layer types to use.
            array_space_type_list: List of array space types to use.
        """


        # Generate a Poisson-distributed set of points.
        points = self._generate_poisson_voronoi_point_distribution(self.size, interpoint_distance)

        available_points = self.get_intersection_of_spaces(map_layer_type_list, array_space_type_list)

        points = [point for point in points if tuple(point) in available_points]

        if points == []:
            points = [list(available_points)[int(len(available_points)*random.random())]]


        # Assign each point in the array to a Voronoi cell.
        new_zones = self._assign_voronoi_cell_numbers(map_layer_type_list, array_space_type_list, points)

        # Grow the Voronoi cells until they can no longer expand.
        total = -1

        while total != 0:
            total = 0
            new_points = []
            for (x, y) in points:
                layer = self.get_map_layer(map_layer_type_list[0])
                array = layer.array
                point_type = array[x][y]

                new_points.extend(self._voronoi_grow_single(map_layer_type_list, 
                                                            array_space_type_list, 
                                                            (x, y), 
                                                            point_type=point_type))
            
            total += len(new_points)
            points = new_points
        
        return new_zones


    # ------------------------- HELPER METHODS ----------------------------------

    def _generate_poisson_voronoi_point_distribution(self, size, interpoint_distance):
        """
        Generates a list of points for creating a voronoi pattern

        Args:
            size: Size of the array.
            interpoint_distance: Minimum distance between points.
        """
        k = 40

        points = self._poisson_disk_sample(size, size, interpoint_distance, k)
        points = np.ndarray.tolist(points)

        for i, (a,b) in enumerate(points):
            points[i] = [int(a), int(b)]
        
        return points

    def _assign_voronoi_cell_numbers(
            self,
            map_layer_type_list: list,
            array_space_type_list: list,
            points: list,
            ):
        """
        Assigns a point value to each point.

        Args:
            map_layer_type_list: List of map layer types to use.
            array_space_type_list: List of array space types to use.
            points: List of points to assign values to.
        """
        new_zones = []

        for i, (x,y) in enumerate(points):
            for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
                layer = self.get_map_layer(map_layer_type)
                layer.set_point(x, y, -i-1-self.global_zone_counter)

            new_zones.append((-i-1-self.global_zone_counter, PlayerId.GAIA))
        
        self.global_zone_counter += len(points)

        return new_zones
    
    def _valid(self,
               map_layer_type_list: list,
               array_space_type_list: list,
               x,
               y):
        """
        Checks that point coordinates appear in the map layers with the correct space type.

        Args:
            map_layer_type_list: List of map layer types to use.
            array_space_type_list: List of array space types to use.
            x: X coordinate of the point.
            y: Y coordinate of the point.
        """
        for map_layer_type, array_space_type in zip(map_layer_type_list, array_space_type_list):
            layer = self.get_map_layer(map_layer_type)
            dictionary = layer.dict
            

            if not array_space_type in dictionary or ((x, y) not in dictionary[array_space_type]):
                return False
        
        return True

    def _voronoi_grow_single(self, 
                            map_layer_type_list: list,
                            array_space_type_list: list,
                            point, 
                            point_type):
        """
        Grows a single cell for creating a voronoi pattern.

        Args:
            map_layer_type_list: List of map layer types to use.
            array_space_type_list: List of array space types to use.
            point: Point to grow from.
            point_type: Point type to assign to the new points.
        """
        new_points = []

        x, y = point

        for i in range(-1,2):
            for j in range(-1,2):
                if abs(i) + abs(j) != 0:
                    
                
                    if (self._valid(map_layer_type_list, array_space_type_list, x+i, y+j) and
                            self.get_map_layer(map_layer_type_list[0]).array[x+i][y+j] != point_type):
                        
                        for map_layer_type in map_layer_type_list:
                            layer = self.get_map_layer(map_layer_type)
                            layer.set_point(x+i, y+j, point_type[0], point_type[1])

                        new_points.append((x+i, y+j))
        
        return new_points

    def _poisson_disk_sample(self, width=1.0, height=1.0, radius=0.025, k=30):
        """
        Generates random points with the poisson disk method

        Args:
            IDK what the variables are LMAO
        """
        # References: Fast Poisson Disk Sampling in Arbitrary Dimensions
        #             Robert Bridson, SIGGRAPH, 2007
        def squared_distance(p0, p1):
            return (p0[0]-p1[0])**2 + (p0[1]-p1[1])**2

        def random_point_around(p, k=1):
            # WARNING: This is not uniform around p but we can live with it
            R = np.random.uniform(radius, 2*radius, k)
            T = np.random.uniform(0, 2*np.pi, k)
            P = np.empty((k, 2))
            P[:, 0] = p[0]+R*np.sin(T)
            P[:, 1] = p[1]+R*np.cos(T)
            return P

        def in_limits(p):
            return 0 <= p[0] < width and 0 <= p[1] < height

        def neighborhood(shape, index, n=2):
            row, col = index
            row0, row1 = max(row-n, 0), min(row+n+1, shape[0])
            col0, col1 = max(col-n, 0), min(col+n+1, shape[1])
            I = np.dstack(np.mgrid[row0:row1, col0:col1])
            I = I.reshape(I.size//2, 2).tolist()
            I.remove([row, col])
            return I

        def in_neighborhood(p):
            i, j = int(p[0]/cellsize), int(p[1]/cellsize)
            if M[i, j]:
                return True
            for (i, j) in N[(i, j)]:
                if M[i, j] and squared_distance(p, P[i, j]) < squared_radius:
                    return True
            return False

        def add_point(p):
            points.append(p)
            i, j = int(p[0]/cellsize), int(p[1]/cellsize)
            P[i, j], M[i, j] = p, True

        # Here `2` corresponds to the number of dimension
        cellsize = radius/np.sqrt(2)
        rows = int(np.ceil(width/cellsize))
        cols = int(np.ceil(height/cellsize))

        # Squared radius because we'll compare squared distance
        squared_radius = radius*radius

        # Positions cells
        P = np.zeros((rows, cols, 2), dtype=np.float32)
        M = np.zeros((rows, cols), dtype=bool)

        # Cache generation for neighborhood
        N = {}
        for i in range(rows):
            for j in range(cols):
                N[(i, j)] = neighborhood(M.shape, (i, j), 2)

        points = []
        add_point((np.random.uniform(width), np.random.uniform(height)))
        while len(points):
            i = np.random.randint(len(points))
            p = points[i]
            del points[i]
            Q = random_point_around(p, k)
            for q in Q:
                if in_limits(q) and not in_neighborhood(q):
                    add_point(q)
        return P[M]
