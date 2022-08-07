from common.constants.constants import DEFAULT_EMPTY_VALUE
from units.wallgenerators.voronoi import generate_voronoi_cells
from common.enums.enum import ValueType
from units.placers.objectplacer import PlacerMixin
from units.placers.templateplacer import TemplatePlacerMixin
from map.map_utils import MapUtilsMixin
from visualizer.visualizer import VisualizerMixin
from AoE2ScenarioParser.datasets.players import PlayerId
from copy import deepcopy

class Map(TemplatePlacerMixin, VisualizerMixin):
    """
    TODO
    """

    def __init__(self, size: int = 100):
        """
        Initializes map object for internal map representation.

        Args:
            size: Size of the map.
        """
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

    def set_point(self, x, y, new_value, value_type: ValueType, player_id: PlayerId):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        # Retrieve correct dictionary and array.
        d = self.get_dictionary_from_value_type(value_type)
        a = self.get_array_from_value_type(value_type)
        
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

    # THIS PROBOBLY BELONGS SOMEWHERE ELSE
    def voronoi(self, interpoint_distance):
        """
        Generates a voronoi cell map.
        """
        self.zone_array = generate_voronoi_cells(self.size, interpoint_distance)
        self.zone_dict = self._create_dict(self.zone_array)

        self.object_array = deepcopy(self.zone_array)
        self.object_dict = self._create_dict(self.object_array)

        self.terrain_array = deepcopy(self.zone_array)
        self.terrain_dict = self._create_dict(self.terrain_array)

        self.decor_array = deepcopy(self.zone_array)
        self.decor_dict = self._create_dict(self.decor_array)