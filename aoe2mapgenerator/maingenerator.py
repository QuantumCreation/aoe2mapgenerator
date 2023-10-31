from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from common.enums.enum import (
    MapLayerType, 
    ObjectSize, 
    GateTypes, 
    TemplateTypes, 
    ObjectRotation, 
    YamlReplacementKeywords,
    CheckPlacementReturnTypes
)
from map.map import Map
from scenario.scenario import Scenario
import numpy as np
import random
from time import time
from common.constants.constants import DEFAULT_EMPTY_VALUE
from common.enums.enum import GateTypes


input_name = "1 vs 7 default.aoe2scenario"
output_name = "0_BASIC_SCENARIO.aoe2scenario"


def main_map_generator(base_scenario_full_path: str, output_file_name:str, output_path: str, **kwargs):
    """
    The main function that generates a map.

    Args:
        base_scenario_path (str): Path to the base scenario file.
        output_file_name (str): Name of the output file.
        **kwargs: Keyword arguments.
    """
    map_size = 300
    map = Map(map_size)
    new_zones = map.voronoi(75,
                [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                [DEFAULT_EMPTY_VALUE, DEFAULT_EMPTY_VALUE, DEFAULT_EMPTY_VALUE, DEFAULT_EMPTY_VALUE])
    
    keys = list(map.get_map_layer(MapLayerType.UNIT).dict.keys())

    for city_zone in keys:
        map.add_borders(
            [MapLayerType.TERRAIN, MapLayerType.UNIT, MapLayerType.ZONE, MapLayerType.DECOR],
            [city_zone, city_zone, city_zone,city_zone],
            TerrainId.ROAD_FUNGUS,
            margin = 2,
            )
        
    counter = 0
    for i, zone in enumerate(new_zones):
        # print(zone)
        counter += 1
        if counter >= 9:
            counter = 1
        
        if random.random() > 0.5:
            build_city(zone, PlayerId(counter))
        else:
            build_snow_forest(zone, PlayerId(counter))
    
    scenario = Scenario(input_name, map, output_path)

    scenario.change_map_size(map_size)
    scenario.write_map()
    scenario.save_file(output_name, output_path)

def build_snow_forest(zone, player_id):
    """
    Build snow forest in zone
    """
    print("BUILD FOREST")
    
    map.place_template(
            'snow_forest.yaml',
            map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
            array_space_type_list = [zone, zone, zone, zone],
            player_id = player_id,
        )

def build_city(zone, player_id):
        """
        Build city in zone
        """
        print("BUILD CITY")

        map.add_borders(
            [MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.UNIT, MapLayerType.DECOR],
            [zone, zone, zone, zone],
            TerrainId.GRASS_2,
            margin = 10
            )

        map.place_template(
                'oak_forest.yaml',
                map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                array_space_type_list = [zone, (TerrainId.GRASS_2, PlayerId.GAIA), zone, zone],
                player_id = player_id,
            )

        map.place_template(
                'walls.yaml',
                map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                array_space_type_list = [zone, zone, zone, zone],
                player_id = player_id,
            )
        
        map.add_borders(
            [MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.UNIT, MapLayerType.DECOR],
            [zone, zone, zone, zone],
            TerrainId.ROAD_FUNGUS,
            margin = 1
            )
        
        city_zones = map.voronoi(35,
                    [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                    [zone, zone, zone, zone],
                )
        
        for city_zone in city_zones:
            map.add_borders(
                [MapLayerType.TERRAIN, MapLayerType.UNIT, MapLayerType.ZONE, MapLayerType.DECOR],
                [city_zone, city_zone, city_zone, city_zone],
                TerrainId.ROAD_FUNGUS,
                margin = 1
                )
            
            map.place_template(
                'oak_forest.yaml',
                map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                array_space_type_list = [city_zone, city_zone, city_zone, city_zone],
            )

            map.place_template(
                'City.yaml',
                map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                array_space_type_list = [city_zone, city_zone, city_zone, city_zone],
                player_id = player_id,
            )