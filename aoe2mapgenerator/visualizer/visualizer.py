import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pylab import matshow
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from common.constants.constants import DEFAULT_EMPTY_VALUE
from copy import deepcopy
from utils.utils import unique_value_list
from common.enums.enum import MapLayerType
from map.map_utils import MapUtilsMixin

class VisualizerMixin(MapUtilsMixin):
    """
    TODO
    """

    def visualize_points(self, mapsize, points, mapping = [], colors = [(255,255,255)]):
        """
        Visualizes a list of points.

        Args:
            mapsize: Size of the map.
            points: Points to plot in (x,y) form.
            mapping: Maps points to object ids.
            colors: TBD
        """
        c = {BuildingInfo.FORTIFIED_WALL:(255,255,255)}

        if len(mapping) < len(points):
            mapping.extend([BuildingInfo.FORTIFIED_WALL]*(len(points)-len(mapping)))

        mat = [[(0,0,0) for i in range(mapsize)] for j in range(mapsize)]
        
        for i, (x,y) in enumerate(points):
            mat[x][y] = c[mapping[i]]
        
        fig, ax = plt.subplots(1,1,facecolor = "white", figsize = (25,25))

        # Transposes the matrix
        mat = [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

        ax.matshow(mat)

    def visualize_mat(self, map_layer_type: MapLayerType, include_zones = False):
        """
        Visualizes a matrix.

        Args:
            map_layer_type: Type of value to visualize.
        """
        fig, ax = plt.subplots(1,1,facecolor = "white", figsize = (25,25))

        mat = deepcopy(self.get_array_from_map_layer_type(map_layer_type))

        for i in range(len(mat)):
            for j in range(len(mat[0])):
                if (not include_zones) and type(mat[i][j]) == int and mat[i][j] < 0:
                    mat[i][j] = 0

        values = unique_value_list(mat)
        remap = dict(zip(values,range(len(values))))

        for i in range(len(mat)):
            for j in range(len(mat[0])):
                mat[i][j] = remap[mat[i][j]]

        ax.hlines(y=np.arange(0, len(mat))+0.5, xmin=np.full(len(mat), 0)-0.5, xmax=np.full(len(mat), len(mat))-0.5, color="black")
        ax.vlines(x=np.arange(0, len(mat))+0.5, ymin=np.full(len(mat), 0)-0.5, ymax=np.full(len(mat), len(mat))-0.5, color="black")

        # Transposes the matrix
        mat = [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

        ax.matshow(mat)

    def visualize_map(self):
        """
        Visualizes a map.

        Args:
            map: Map to visualize
        """
        fig, ax = plt.subplots(1,1,facecolor = "white", figsize = (25,25))
        terrain_matrix = deepcopy(self.get_map_layer(MapLayerType.TERRAIN).array)
        object_matrix = deepcopy(self.get_map_layer(MapLayerType.UNIT).array)

        mat = terrain_matrix

        values = set()

        for i in range(len(mat)):
            for j in range(len(mat[0])):
                if type(mat[i][j]) == int and mat[i][j] < 0:
                    mat[i][j] = DEFAULT_EMPTY_VALUE
                values.add(terrain_matrix[i][j])
                values.add(object_matrix[i][j])

        for i in range(len(mat)):
            for j in range(len(mat[0])):
                if object_matrix[i][j] != DEFAULT_EMPTY_VALUE:
                    mat[i][j] = object_matrix[i][j]
        
        
        values = list(values)
        remap = dict(zip(values,range(len(values))))

        for i in range(len(mat)):
            for j in range(len(mat[0])):
                mat[i][j] = remap[mat[i][j]]

        ax.hlines(y=np.arange(0, len(mat))+0.5, xmin=np.full(len(mat), 0)-0.5, xmax=np.full(len(mat), len(mat))-0.5, color="black")
        ax.vlines(x=np.arange(0, len(mat))+0.5, ymin=np.full(len(mat), 0)-0.5, ymax=np.full(len(mat), len(mat))-0.5, color="black")

        # Transposes the matrix
        mat = [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

        ax.matshow(mat)


