from re import I
import numpy as np
from typing import Union, Callable
import functools
from AoE2ScenarioParser.datasets.players import PlayerId
from map.map_utils import MapUtilsMixin

class VoronoiGeneratorMixin(MapUtilsMixin):
    """
    TODO
    """
    global_zone_counter = 0

    def generate_voronoi_cells(
            self, 
            size: int, 
            interpoint_distance: int,
            array = None
            ):
        """
        Generates an array of voronoi shapes, with numbers starting from -1 and going down.

        Args:
            size: Size of an nxn array.
            interpoint_distance: Minimum distance between points.
        """
        if array is None:
            # Initialize the array with zeros.
            array = [[0 for i in range(size)] for j in range(size)]

            # Generate a Poisson-distributed set of points.
            points = self._generate_poisson_voronoi_point_distribution(size, interpoint_distance)
        else:
            # Generate a Poisson-distributed set of points.
            points = self._generate_poisson_voronoi_point_distribution(len(array), interpoint_distance)

        # Assign each point in the array to a Voronoi cell.
        self._assign_voronoi_cell_numbers(array, points)

        # Grow the Voronoi cells until they can no longer expand.
        total = -1

        while total != 0:
            total = 0
            new_points = []
            for (x, y) in points:
                new_points.extend(self._voronoi_grow_single(array, (x, y), point_type=array[x][y]))
            
            total += len(new_points)
            points = new_points
        
        return array

    # ------------------------- HELPER METHODS ----------------------------------

    def _generate_poisson_voronoi_point_distribution(self, size, interpoint_distance):
        """
        Generates a list of points for creating a voronoi pattern
        """
        k = 40

        points = self._poisson_disk_sample(size,size,interpoint_distance,k)
        points = np.ndarray.tolist(points)

        for i, (a,b) in enumerate(points):
            points[i] = [int(a), int(b)]
        
        return points

    def _assign_voronoi_cell_numbers(
            self,
            array,
            points,
            ):
        """
        Assigns a point value to each point.

        Args:
            array: Array representing the total space.
            points: Points used to create the Voronoi texture.
        """
        for i, (x,y) in enumerate(points):
            if self._valid(array,x,y):
                array[x][y] = -(i+1)-self.global_zone_counter
        
        self.global_zone_counter += len(points)
    
        return array

    def _valid(self, array, x, y):
        """
        Checks that point coordinates are valid.

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        return (0<=x<len(array)) and (0<=y<len(array[0]))

    def _voronoi_grow_single(self, array, point, point_type):
        """
        Grows a single cell for creating a voronoi pattern.

        Args:
            array: Input array to create the pattern.
            point: Point with (x,y) coordinates.
            point_type: Type of the cell that is being expanded. Should have unique ID.
        """
        new_points = []

        x, y = point

        for i in range(-1,2):
            for j in range(-1,2):
                if abs(i) + abs(j) != 0:
                    if self._valid(array, x+i, y+j) and array[x+i][y+j] == 0:
                        array[x+i][y+j] = point_type
                        new_points.append([x+i,y+j])
        
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
