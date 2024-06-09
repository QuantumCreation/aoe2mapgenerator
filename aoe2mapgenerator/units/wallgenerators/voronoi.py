"""
TODO: Add a description of this file.
"""

import random

import numpy as np
from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.point_manager import PointManager
import numpy as np
from scipy.ndimage import distance_transform_edt


class VoronoiGenerator(PlacerBase):
    """
    Class for generating voronoi patterns.
    """

    global_zone_counter = 0

    def __init__(self, aoe2_map: Map):
        super().__init__(aoe2_map)
        self.size = aoe2_map.size

    def generate_voronoi_cells(
        self,
        point_manager: PointManager,
        interpoint_distance: int,
        map_layer_type: MapLayerType,
    ):
        """
        Generates an array of voronoi shapes, with numbers starting from -1 and going down.

        Args:
            interpoint_distance (int): Minimum distance between points.
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns:
            list: List of the new zones.
        """

        # Create a voronoi diagram.
        available_points = point_manager.get_point_list_copy()

        if len(available_points) == 0:
            return []

        height = point_manager.get_x_point_range()
        width = point_manager.get_y_point_range()
        top_left_corner = point_manager.get_theoretical_top_left_corner_point()

        # Generate a Poisson-distributed set of points.
        voronoi_seed_points = self._generate_poisson_voronoi_point_distribution(
            width, height, interpoint_distance
        )

        # Filter out points that are not in the available points.
        voronoi_seed_points = [
            point
            for point in voronoi_seed_points
            if (point[0] + top_left_corner[0], point[1] + top_left_corner[1])
            in available_points
        ]

        if voronoi_seed_points == []:
            # If there are no points, grab a random point from the available points.
            voronoi_seed_points = [
                available_points[int(len(available_points) * random.random())]
            ]

        new_zones = dict()

        # Translate the points to the top left corner
        # voronoi_seed_points = [
        #     (x + top_left_corner[0], y + top_left_corner[1])
        #     for x, y in voronoi_seed_points
        # ]

        voronoi_zones = generate_voronoi_l1(width, height, voronoi_seed_points)

        for point in available_points:
            try:
                x_voronoi = point[0] - top_left_corner[0]
                y_voronoi = point[1] - top_left_corner[1]
                zone_value = voronoi_zones[x_voronoi][y_voronoi]
            except IndexError:
                continue

            self._place(
                point_manager,
                map_layer_type,
                point,
                zone_value,
                PlayerId.GAIA,
                0,
            )

            # This code to create the object is repeated in the map set point function
            # There is likely a better way to do this, but I'm unsure what it is
            new_obj = MapObject(zone_value, PlayerId.GAIA)

            if new_obj not in new_zones:
                new_zones[new_obj] = ""

        return list(new_zones.keys())

    def manhattan_distance(self, point1, point2):
        """
        Calculates the manhattan distance between two points.
        """
        return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

    # ------------------------- HELPER METHODS ----------------------------------

    def _generate_poisson_voronoi_point_distribution(
        self, width: int, height: int, interpoint_distance: int
    ) -> list[tuple[int, int]]:
        """
        Generates a list of points for creating a voronoi pattern

        Args:
            size: Size of the array.
            interpoint_distance: Minimum distance between points.
        """
        k = 40

        points = self._poisson_disk_sample(width, height, interpoint_distance, k)
        points = np.ndarray.tolist(points)

        for i, (a, b) in enumerate(points):
            points[i] = [int(a), int(b)]

        return points

    def _poisson_disk_sample(
        self, width=1.0, height=1.0, radius=0.025, k=30
    ) -> np.ndarray:
        """
        Generates random points with the poisson disk method

        Args:
            IDK what the variables are LMAO
        """

        # References: Fast Poisson Disk Sampling in Arbitrary Dimensions
        #             Robert Bridson, SIGGRAPH, 2007
        def squared_distance(p0, p1):
            return (p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2

        def random_point_around(p, k=1):
            # WARNING: This is not uniform around p but we can live with it
            R = np.random.uniform(radius, 2 * radius, k)
            T = np.random.uniform(0, 2 * np.pi, k)
            P = np.empty((k, 2))
            P[:, 0] = p[0] + R * np.sin(T)
            P[:, 1] = p[1] + R * np.cos(T)
            return P

        def in_limits(p):
            return 0 <= p[0] < height and 0 <= p[1] < width

        def neighborhood(shape, index, n=2):
            row, col = index
            row0, row1 = max(row - n, 0), min(row + n + 1, shape[0])
            col0, col1 = max(col - n, 0), min(col + n + 1, shape[1])
            I = np.dstack(np.mgrid[row0:row1, col0:col1])
            I = I.reshape(I.size // 2, 2).tolist()
            I.remove([row, col])
            return I

        def in_neighborhood(p):
            i, j = int(p[0] / cellsize), int(p[1] / cellsize)
            if m_array[i, j]:
                return True
            for i, j in n_dict[(i, j)]:
                if (
                    m_array[i, j]
                    and squared_distance(p, p_array[i, j]) < squared_radius
                ):
                    return True
            return False

        def add_point(p):
            points.append(p)
            i, j = int(p[0] / cellsize), int(p[1] / cellsize)
            p_array[i, j], m_array[i, j] = p, True

        # Here `2` corresponds to the number of dimension
        cellsize = radius / np.sqrt(2)
        rows = int(np.ceil(height / cellsize))
        cols = int(np.ceil(width / cellsize))

        # Squared radius because we'll compare squared distance
        squared_radius = radius * radius

        # Positions cells
        p_array = np.zeros((rows, cols, 2), dtype=np.float32)
        m_array = np.zeros((rows, cols), dtype=bool)

        # Cache generation for neighborhood
        n_dict = {}
        for i in range(rows):
            for j in range(cols):
                n_dict[(i, j)] = neighborhood(m_array.shape, (i, j), 2)

        points: list = []
        add_point((np.random.uniform(height), np.random.uniform(width)))
        while len(points) > 0:
            index: int = np.random.randint(len(points))
            p = points[index]
            del points[index]
            Q = random_point_around(p, k)
            for q in Q:
                if in_limits(q) and not in_neighborhood(q):
                    add_point(q)
        return p_array[m_array]


def generate_voronoi_l2(
    grid_width: int, grid_height: int, seed_points: list[tuple[int, int]]
) -> list[list[int]]:
    """
    Generate a Voronoi diagram on a cell grid.

    Args:
        grid_size (tuple): The size of the grid (rows, columns).
        seed_points (list): List of (x, y) tuples representing seed points.

    Returns:
        np.ndarray: A 2D array with the same size as grid, where each cell contains the index of the nearest seed point.
    """
    rows, cols = grid_width, grid_height
    seeds = np.array(seed_points)

    # Initialize an array to hold the seed indices
    grid = np.full((rows, cols), -1)

    # Place seed indices on the grid
    for idx, (y, x) in enumerate(seeds):
        grid[x, y] = idx

    # Create an array to hold the distances
    distance_grid = np.full((rows, cols), np.inf)
    indices_grid = np.zeros((rows, cols), dtype=int)

    # Compute the Euclidean Distance Transform for each seed
    for idx, (y, x) in enumerate(seeds):
        mask = grid == idx
        distances = distance_transform_edt(
            ~mask, return_distances=True, return_indices=False
        )
        update_mask = distances < distance_grid
        distance_grid[update_mask] = distances[update_mask]
        indices_grid[update_mask] = idx

    return indices_grid.tolist()


def generate_voronoi_l1(
    grid_width: int, grid_height: int, seed_points: list[tuple[int, int]]
) -> list[list[int]]:
    """
    Generate a Voronoi diagram on a cell grid using L1 distance.

    Args:
        grid_width (int): The width of the grid.
        grid_height (int): The height of the grid.
        seed_points (list): List of (x, y) tuples representing seed points.

    Returns:
        list[list[int]]: A 2D list where each cell contains the index of the nearest seed point incremented by 1.
    """
    # rows, cols = grid_height, grid_width
    rows, cols = grid_width, grid_height

    seeds = np.array(seed_points)

    # Create a coordinate grid
    x, y = np.meshgrid(np.arange(cols), np.arange(rows))
    coordinates = np.stack([x, y], axis=-1)

    # Initialize distance and index grids
    distance_grid = np.full((rows, cols), np.inf)
    index_grid = np.full((rows, cols), -1)

    # Compute L1 distance for each seed point and update grids
    for idx, (sx, sy) in enumerate(seeds):
        distances = np.abs(coordinates[..., 0] - sx) + np.abs(coordinates[..., 1] - sy)
        update_mask = distances < distance_grid
        distance_grid[update_mask] = distances[update_mask]
        index_grid[update_mask] = idx

    # Increment every element by one so that it doesn't match the empty object value
    index_grid += 1

    return index_grid.transpose().tolist()
