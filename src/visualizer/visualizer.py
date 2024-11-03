"""
TODO: Add description
"""

from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
from AoE2ScenarioParser.datasets.buildings import BuildingInfo

from aoe2mapgenerator.src.common.constants.constants import DEFAULT_EMPTY_VALUE
from aoe2mapgenerator.src.common.enums.enum import MapLayerType
from aoe2mapgenerator.src.map.map import Map
from aoe2mapgenerator.src.utils.utils import unique_value_list
from aoe2mapgenerator.src.units.placers.placer_configs import VisualizeMapConfig
from aoe2mapgenerator.src.map.map_object import MapObject


class Visualizer:
    """
    TODO
    """

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map

    def visualize_points(self, mapsize, points):
        """
        Visualizes a list of points.

        Args:
            mapsize: Size of the map.
            points: Points to plot in (x,y) form.
            mapping: Maps points to object ids.
            colors: TBD
        """
        mapping = []

        c = {BuildingInfo.FORTIFIED_WALL: (255, 255, 255)}

        if len(mapping) < len(points):
            mapping.extend([BuildingInfo.FORTIFIED_WALL] * (len(points) - len(mapping)))

        mat = [[(0, 0, 0) for i in range(mapsize)] for j in range(mapsize)]

        for i, (x, y) in enumerate(points):
            mat[x][y] = c[mapping[i]]

        fig, ax = plt.subplots(1, 1, facecolor="white", figsize=(20, 20))

        # Transposes the matrix
        mat = [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

        ax.matshow(mat)

    def visualize_mat(
        self,
        configuration: VisualizeMapConfig,
    ):
        """
        Visualizes a matrix.

        Args:
            map_layer_type: Type of value to visualize.
        """
        map_layer_type = configuration.map_layer_type
        include_zones = configuration.include_zones
        transpose = configuration.transpose
        fig_size = configuration.fig_size
        include_legend = configuration.include_legend
        anchor = configuration.anchor

        # Creat the figure
        fig, ax = plt.subplots(1, 1, facecolor="white", figsize=fig_size)

        # Make a copy of the matrix since we will be modifying it
        mat = deepcopy(self.map.get_array_from_map_layer_type(map_layer_type))

        # Get the unique values in the matrix
        unique_values: list[MapObject] = unique_value_list(mat)
        # Creates a map from unique values to integers
        remap = dict(zip(unique_values, range(len(unique_values))))

        # Create a colormap
        cmap = plt.get_cmap("viridis", len(unique_values))
        colors = [cmap(remap[val]) for val in remap]

        for i, row in enumerate(mat):
            for j, value in enumerate(row):
                mat[i][j] = colors[remap[value]]

        ax.hlines(
            y=np.arange(0, len(mat)) + 0.5,
            xmin=np.full(len(mat), 0) - 0.5,
            xmax=np.full(len(mat), len(mat)) - 0.5,
            color="black",
        )
        ax.vlines(
            x=np.arange(0, len(mat)) + 0.5,
            ymin=np.full(len(mat), 0) - 0.5,
            ymax=np.full(len(mat), len(mat)) - 0.5,
            color="black",
        )

        if include_legend:
            handles = [
                plt.Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    markerfacecolor=colors[remap[value]],
                    markersize=10,
                )
                for value in unique_values
            ]
            labels = [
                f"Name: {v.get_obj_type()}, Player: {v.get_player_id()}"
                for v in unique_values
            ]
            ax.legend(
                handles,
                labels,
                loc="upper center",
                bbox_to_anchor=anchor,
                fancybox=True,
                shadow=True,
            )

        # Transposes the matrix to match aoe2 map
        if transpose:
            mat = [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

        ax.matshow(mat)

    def visualize_map(self):
        """
        Visualizes a map.

        Args:
            map: Map to visualize
        """
        fig, ax = plt.subplots(1, 1, facecolor="white", figsize=(25, 25))
        terrain_matrix = deepcopy(self.get_map_layer(MapLayerType.TERRAIN).array)
        object_matrix = deepcopy(self.get_map_layer(MapLayerType.UNIT).array)

        mat = terrain_matrix

        values = set()

        for i, row in enumerate(mat):
            for j, _ in enumerate(row):
                if isinstance(mat[i][j], int) and mat[i][j] < 0:
                    mat[i][j] = DEFAULT_EMPTY_VALUE

                values.add(terrain_matrix[i][j])
                values.add(object_matrix[i][j])

        for i, row in enumerate(mat):
            for j, _ in enumerate(row):
                if object_matrix[i][j] != DEFAULT_EMPTY_VALUE:
                    mat[i][j] = object_matrix[i][j]

        values = list(values)
        remap = dict(zip(values, range(len(values))))

        for i, row in enumerate(mat):
            for j, _ in enumerate(row):
                mat[i][j] = remap[mat[i][j]]

        ax.hlines(
            y=np.arange(0, len(mat)) + 0.5,
            xmin=np.full(len(mat), 0) - 0.5,
            xmax=np.full(len(mat), len(mat)) - 0.5,
            color="black",
        )
        ax.vlines(
            x=np.arange(0, len(mat)) + 0.5,
            ymin=np.full(len(mat), 0) - 0.5,
            ymax=np.full(len(mat), len(mat)) - 0.5,
            color="black",
        )

        # Transposes the matrix
        mat = [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

        ax.matshow(mat)
