
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId

class map():

    def __init__(self, size = 256):
        """
        Initializes map object for internal map representation.

        Args:
            size: Size of the map.
        """
        self.map_array = [[0 for i in range(size)] for j in range(size)]
        self.map_dict = self.create_set(self.map_array)
        self.terrain_array = [[0 for i in range(size)] for j in range(size)]
        self.terrain_dict = self.create_set(self.terrain_array)

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
    
    def set_point(self, x, y, new_value):
        """
        Takes an x and y coordinate and updates both the array and set representation.
        """
        if new_value in TerrainId:
            d = self.terrain_dict
            a = self.terrain_array
        else:
            d = self.map_dict
            a = self.map_array
        
        d[a[x][y]].remove((x,y))

        if len(d[a[x][y]]) == 0:
            d.pop(a[x][y], None)

        a[x][y] = new_value

        if new_value in d:
            d[a[x][y]].add((x,y))
        else:
            d[a[x][y]] = {(x,y)}

