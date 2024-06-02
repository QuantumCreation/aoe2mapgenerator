from aoe2mapgenerator.map.map import Map
from typing import Union
from aoe2mapgenerator.common.enums.enum import MapLayerType

class MapManager():

    def __init__(self, map: Map):
        self.map = map
        self.templates = []


    def get_map(self):
        return self.map
    
    def get_map_layer(self, map_layer_type: MapLayerType):
        return self.map.get_map_layer(map_layer_type)

    def get_dictionary(self, map_layer_type: MapLayerType) -> dict:
        return self.map.get_map_layer(map_layer_type).get_dict()
    
    def get_array(self, map_layer_type: Union[MapLayerType, int]) -> list:
        return self.map.get_map_layer(map_layer_type).get_array()
    