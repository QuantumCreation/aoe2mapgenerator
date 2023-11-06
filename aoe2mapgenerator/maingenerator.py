from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.common.enums.enum import (
    MapLayerType, 
    ObjectSize, 
    GateTypes, 
    TemplateTypes, 
    ObjectRotation, 
    YamlReplacementKeywords,
    CheckPlacementReturnTypes
)
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.scenario.scenario import Scenario
import numpy as np
import random
from aoe2mapgenerator.common.constants.constants import DEFAULT_EMPTY_VALUE

def main_map_generator(base_scenario_full_path: str, 
                       output_file_full_path: str,
                       template_dir: str,
                       map_size: int = 200, 
                       **kwargs):
    """
    The main function that generates a map.

    Args:
        base_scenario_full_path (str): Full path to the base scenario file.
        output_file_full_path (str): Full path to the output scenario file.
        template_dir (str): Full path to the template directory.
        **kwargs: Keyword arguments.
    """
    # map_size = 300
    map = Map(map_size)
    new_zones = map.voronoi(75)
    
    keys = list(map.get_map_layer(MapLayerType.UNIT).dict.keys())

    for city_zone in keys:
        map.add_borders(
            [MapLayerType.TERRAIN, MapLayerType.UNIT, MapLayerType.ZONE, MapLayerType.DECOR],
            [city_zone, city_zone, city_zone, city_zone],
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
            build_city(zone, PlayerId(counter), map, template_dir)
        else:
            build_snow_forest(zone, PlayerId(counter), map, template_dir)
    
    return map

def save_and_write_map(map: Map, base_scenario_full_path: str, output_file_full_path: str) -> Scenario:
    """
    Saves and writes the map to a scenario file.
    
    Args:
        map (Map): Map object to save and write.
        base_scenario_full_path (str): Full path to the base scenario file.
        output_file_full_path (str): Full path to the output scenario file.
    
    Returns:
        Scenario: Scenario object.
    """
    scenario = Scenario(map, base_scenario_full_path)
    scenario.change_map_size(map.size)
    scenario.write_map()
    scenario.save_file(output_file_full_path)

    return scenario

def build_snow_forest(zone, player_id, map, base_template_dir):
    """
    Build snow forest in zone
    """
    print("BUILD FOREST")
    
    map.place_template(
            'snow_forest.yaml',
            map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
            array_space_type_list = [zone, zone, zone, zone],
            player_id = player_id,
            base_template_dir = base_template_dir
        )

def build_city(zone, player_id, map, base_template_dir):
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
                base_template_dir = base_template_dir
            )

        map.place_template(
                'walls.yaml',
                map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                array_space_type_list = [zone, zone, zone, zone],
                player_id = player_id,
                base_template_dir = base_template_dir
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
                base_template_dir = base_template_dir
            )

            map.place_template(
                'City.yaml',
                map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
                array_space_type_list = [city_zone, city_zone, city_zone, city_zone],
                player_id = player_id,
                base_template_dir = base_template_dir
            )