from aoe2mapgenerator.map.map import Map
from typing import Union
from aoe2mapgenerator.common.enums.enum import MapLayerType

class MapManager():

    def __init__(self, map: Map):
        self.map = map
    
    def get_map(self):
        return self.map

    def get_dictionary(self, map_layer_type: MapLayerType) -> dict:
        return self.map.get_map_layer(map_layer_type).dict
    
    def get_array(self, map_layer_type: Union[MapLayerType, int]) -> list:
        return self.map.get_map_layer(map_layer_type).array
    
    def get_matching_points(self, map_layer_type: MapLayerType, array_space_type: any) -> None:
    