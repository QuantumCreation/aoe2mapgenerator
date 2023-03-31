from common.constants.constants import DEFAULT_EMPTY_VALUE
from units.wallgenerators.voronoi import VoronoiGeneratorMixin
from common.enums.enum import ValueType
from units.placers.objectplacer import PlacerMixin
from units.placers.templateplacer import TemplatePlacerMixin
from map.map_utils import MapUtilsMixin
from visualizer.visualizer import VisualizerMixin
from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy
from typing import Union, Callable

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
        self.object_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.object_dict = self._create_dict(self.object_array)
        self.terrain_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.terrain_dict = self._create_dict(self.terrain_array)
        self.decor_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.decor_dict = self._create_dict(self.decor_array)
        self.zone_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.zone_dict = self._create_dict(self.zone_array)
        self.elevation_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.elevation_dict = self._create_dict(self.elevation_array)

    def _create_dict(self, array: list[list[object]]):
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

    # THIS PROBOBLY BELONGS SOMEWHERE ELSE
    def voronoi(self, interpoint_distance):
        """
        Generates a voronoi cell map.
        """
        self.zone_array = self.generate_voronoi_cells(self.size, interpoint_distance)
        self.zone_dict = self._create_dict(self.zone_array)

        self.object_array = deepcopy(self.zone_array)
        self.object_dict = self._create_dict(self.object_array)

        self.terrain_array = deepcopy(self.zone_array)
        self.terrain_dict = self._create_dict(self.terrain_array)

        self.decor_array = deepcopy(self.zone_array)
        self.decor_dict = self._create_dict(self.decor_array)

class MapLayer():
    """
    Single Map type constructor.
    """

    def __init__(self, layer: ValueType, size: int = 100, array = [], dict = {}):
        
        self.layer = layer
        self.size = size
        
        self.array = array
        self.dict = dict


        
        self.object_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.object_dict = self._create_dict(self.object_array)
        self.terrain_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.terrain_dict = self._create_dict(self.terrain_array)
        self.decor_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.decor_dict = self._create_dict(self.decor_array)
        self.zone_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.zone_dict = self._create_dict(self.zone_array)
        self.elevation_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.elevation_dict = self._create_dict(self.elevation_array)

