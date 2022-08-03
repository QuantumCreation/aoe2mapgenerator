
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from matplotlib.pyplot import new_figure_manager
from common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_EMPTY_VALUE


class map():

    def __init__(self, size = 256):
        """
        Initializes map object for internal map representation.

        Args:
            size: Size of the map.
        """
        self.object_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.object_dict = self.create_set(self.object_array)
        self.terrain_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.terrain_dict = self.create_set(self.terrain_array)
        self.decor_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.decor_dict = self.create_set(self.decor_array)
        self.zone_array = [[DEFAULT_EMPTY_VALUE for i in range(size)] for j in range(size)]
        self.zone_dict = self.create_set(self.zone_array)

    def create_set(self, array):
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
    

    def get_point_type(self, new_value):
        """
        Returns the type of the new value point.

        Args:
            new_value: The value of the point being added.
        """
        
    def set_point(self, x, y, new_value):
        """
        Takes an x and y coordinate and updates both the array and set representation.

        Args:
            x: X coordinate.
            y: Y coordinate.
            new_value: Value to set the point to.
        """
        # Retrieve correct dictionary and array.
        if type(new_value) == int:
            d = self.zone_dict
            a = self.zone_array
        elif new_value in TerrainId:
            d = self.terrain_dict
            a = self.terrain_array
        elif any(new_value in enum for enum in {UnitInfo, BuildingInfo, OtherInfo}):
            d = self.object_dict
            a = self.object_array
        else:
            d = self.decor_dict
            a = self.decor_array
        
        # Remove element from the dictionary.
        d[a[x][y]].remove((x,y))

        # Remove entire dictionary entry if there are not elements left.
        if len(d[a[x][y]]) == 0:
            d.pop(a[x][y], None)

        # Assign new value to the array.
        a[x][y] = new_value

        # Add the value to the dictionary.
        if new_value in d:
            d[a[x][y]].add((x,y))
        else:
            d[a[x][y]] = {(x,y)}

