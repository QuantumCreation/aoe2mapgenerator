"""
TODO: Add a description of this file.
"""

import random

import numpy as np
from AoE2ScenarioParser.datasets.players import PlayerId
from scipy.ndimage import distance_transform_edt

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.units.placers.placer_configs import (
    PlaceGroupsConfig,
    AddBordersConfig,
    VoronoiGeneratorConfig,
)
from typing import List


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
        configuration: VoronoiGeneratorConfig,
    ) -> list[MapObject]:
        """
        Generates an array of voronoi shapes, with numbers starting from -1 and going down.

        Args:
            interpoint_distance (int): Minimum distance between points.
            map_layer_type_list (list): List of map layer types to use.
            array_space_type_list (list): List of array space types to use.

        Returns:
            list: List of the new zones.
        """
        point_collection = configuration.point_collection
        interpoint_distance = configuration.interpoint_distance
        map_layer_type = configuration.map_layer_type

        available_points = point_collection.get_point_list_copy()
        if len(available_points) == 0:
            return []

        height = point_collection.get_x_point_range()
        width = point_collection.get_y_point_range()
        top_left_corner = point_collection.get_theoretical_top_left_corner_point()

        voronoi_seed_points = self._generate_filtered_voronoi_seed_points(
            width, height, interpoint_distance, available_points, top_left_corner
        )

        if not voronoi_seed_points:
            voronoi_seed_points = [
                available_points[int(len(available_points) * random.random())]
            ]

        voronoi_zones = generate_voronoi_l1(
            width, height, voronoi_seed_points, zone_shift=self.global_zone_counter
        )

        return self._create_zones_from_voronoi(
            voronoi_zones,
            available_points,
            top_left_corner,
            map_layer_type,
            point_collection,
        )

    def _generate_filtered_voronoi_seed_points(
        self, width, height, interpoint_distance, available_points, top_left_corner
    ) -> list[tuple[int, int]]:
        """
        Generates and filters voronoi seed points based on available points.

        Args:
            width (int): Width of the area.
            height (int): Height of the area.
            interpoint_distance (int): Minimum distance between points.
            available_points (list): List of available points.
            top_left_corner (tuple): Top left corner point.

        Returns:
            list: Filtered voronoi seed points.
        """
        voronoi_seed_points = self._generate_poisson_voronoi_point_distribution(
            width, height, interpoint_distance
        )

        filtered_points = []
        for point in voronoi_seed_points:
            adjusted_point = (
                point[0] + top_left_corner[0],
                point[1] + top_left_corner[1],
            )
            if adjusted_point in available_points:
                filtered_points.append(point)

        return filtered_points

    def _create_zones_from_voronoi(
        self,
        voronoi_zones,
        available_points,
        top_left_corner,
        map_layer_type,
        point_collection,
    ) -> list[MapObject]:
        """
        Creates zones from voronoi zones and places them on the map.

        Args:
            voronoi_zones (list): Voronoi zones.
            available_points (list): List of available points.
            top_left_corner (tuple): Top left corner point.
            map_layer_type (MapLayerType): Map layer type.
            point_collection (PointCollection): Point collection.

        Returns:
            list: List of new zones.
        """
        new_zones = dict()

        for point in available_points:
            try:
                x_voronoi = point[0] - top_left_corner[0]
                y_voronoi = point[1] - top_left_corner[1]
                zone_value = voronoi_zones[x_voronoi][y_voronoi]
            except IndexError:
                continue

            self._place_single(
                point_collection,
                map_layer_type,
                point,
                zone_value,
                PlayerId.GAIA,
                0,
            )

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
    ) -> List[tuple[int, int]]:
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

        return list(points)

    def _poisson_disk_sample(
        self, width=1.0, height=1.0, radius=0.025, k=30
    ) -> np.ndarray:
        """
        Generates random points using the Poisson disk sampling method.

        Implements the algorithm described in:
            "Fast Poisson Disk Sampling in Arbitrary Dimensions"
            Robert Bridson, SIGGRAPH 2007.

        Args:
            width: Width of the sampling domain (number of columns).
            height: Height of the sampling domain (number of rows).
            radius: Minimum distance between any two sample points.
            k: Number of candidate points tested per accepted point before
               the point is considered inactive. Higher k gives better
               packing at the cost of more iterations (recommended: 30).

        Returns:
            np.ndarray of shape (N, 2) containing accepted sample coordinates,
            where each row is (row_coord, col_coord) within [0, height) × [0, width).
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
            # O(1) removal: swap chosen element with tail, then pop.
            # Preserves identical statistical behaviour; avoids O(n) list shift.
            points[index] = points[-1]
            p = points.pop()
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
    grid_width: int,
    grid_height: int,
    seed_points: list[tuple[int, int]],
    zone_shift: int = 1,
) -> list[list[int]]:
    """
    Generate a Voronoi diagram on a cell grid using L1 (Manhattan) distance.

    Fully vectorised: all seed distances are computed in a single NumPy
    broadcast operation instead of a per-seed loop.

    Tie-breaking: when two seeds are equidistant from a tile the seed with the
    lower list index wins.  This is identical to the former per-seed loop which
    used strict ``<`` comparison, and to ``np.argmin`` semantics on the stacked
    distance array.

    Args:
        grid_width (int): Width of the grid (number of rows in the returned 2D list).
        grid_height (int): Height of the grid (number of columns in each row).
        seed_points (list): List of (x, y) tuples representing seed points.
        zone_shift (int): Added to every zone index; zones start at ``zone_shift``
            rather than 0 so they do not alias with the empty-tile sentinel.

    Returns:
        list[list[int]]: 2D list where each cell contains the index of the
        nearest seed point + zone_shift.
    """
    rows, cols = grid_width, grid_height

    if not seed_points:
        return [[zone_shift] * cols for _ in range(rows)]

    seeds = np.array(seed_points, dtype=np.int32)  # (n_seeds, 2)

    # Coordinate grids: col_idx[i, j] = j, row_idx[i, j] = i
    # Mirrors the original: x, y = np.meshgrid(np.arange(cols), np.arange(rows))
    # where x[i,j] = j (col component) and y[i,j] = i (row component).
    col_idx, row_idx = np.meshgrid(
        np.arange(cols, dtype=np.int32),
        np.arange(rows, dtype=np.int32),
    )  # both shape (rows, cols)

    # Broadcast seeds to (n_seeds, 1, 1) for simultaneous distance computation.
    seeds_sx = seeds[:, 0][:, np.newaxis, np.newaxis]  # col component of seeds
    seeds_sy = seeds[:, 1][:, np.newaxis, np.newaxis]  # row component of seeds

    # all_distances[k, i, j] = L1 distance from grid tile (i, j) to seed k.
    # Shape: (n_seeds, rows, cols), dtype=int32.
    all_distances = (
        np.abs(col_idx[np.newaxis] - seeds_sx)
        + np.abs(row_idx[np.newaxis] - seeds_sy)
    )

    # argmin along the seed axis: ties broken by lowest seed index (first wins),
    # identical to the former loop with strict < comparison.
    index_grid = np.argmin(all_distances, axis=0)  # (rows, cols)

    # Shift so zone indices start at zone_shift.
    index_grid = index_grid + zone_shift

    return index_grid.transpose().tolist()

