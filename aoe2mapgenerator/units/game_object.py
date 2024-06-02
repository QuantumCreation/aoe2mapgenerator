from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.other import OtherInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from aoe2mapgenerator.common.enums.enum import AOE2Object

class GameObject():

    def __init__(self, player_id: PlayerId = PlayerId.GAIA, object: AOE2Object | int = None):
        self.player_id = player_id
        self.object = object