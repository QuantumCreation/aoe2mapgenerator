from AoE2ScenarioParser.objects.managers.trigger_manager import TriggerManager
from AoE2ScenarioParser.objects.support.new_effect import NewEffectSupport
from AoE2ScenarioParser.objects.data_objects.trigger import Trigger
from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.players import PlayerId



class TriggerObject:

    def __init__ (self, scenario: AoE2DEScenario) -> None:
        self.scenario = scenario
        self.trigger_manager = scenario.trigger_manager

    def create_objects_in_area(self, x1: int, y1: int, x2: int, y2: int, object: UnitInfo, player_id: PlayerId, looping: bool = True):
            trigger = self.trigger_manager.add_trigger("Create Objects In Area")

            for i in range(x1, x2+1):
                for j in range(y1, y2+1):
                    trigger.new_effect.create_object(object_list_unit_id=object.ID, source_player=player_id, location_x=i, location_y=j)

            trigger.looping = looping
    
    def teleport_object_to_point(self, x: int, y: int, target_x: int, target_y: int, player_id: PlayerId, looping: bool = True):
            trigger = self.trigger_manager.add_trigger("Teleport Object To Point")

            trigger.new_effect.teleport_object(source_player=player_id, location_x=target_x, location_y=target_y, area_x1=x, area_y1=y, area_x2=x, area_y2=y)

            trigger.looping = looping
    
    def teleport_objects_in_area(self, x1: int, y1: int, x2: int, y2: int, target_x: int, target_y: int, player_id: PlayerId, looping = True):
            trigger = self.trigger_manager.add_trigger("Teleport Objects In Area")

            trigger.new_effect.teleport_object(source_player=player_id, location_x=target_x, location_y=target_y, area_x1=x1, area_y1=y1, area_x2=x2, area_y2=y2)

            trigger.looping = looping
    
    def teleport_objects_from_area_to_area(self, x11: int, y11: int, x21: int, y21: int, x12: int, y12: int, x22: int, y22: int, player_id: PlayerId, looping: bool = True):
        trigger = self.trigger_manager.add_trigger("Teleport Objects From Area To Area")

        for i in range(x12, x22+1):
            for j in range(y12, y22+1):
                trigger.new_effect.teleport_object(source_player=player_id, location_x=i, location_y=j, area_x1=x11, area_y1=y11, area_x2=x21, area_y2=y21)

        trigger.looping = looping

    def spawn_infinite_waves(self, ):
        trigger = self.trigger_manager.add_trigger("Spawn Waves")

        trigger.create_objects_in_area(0,0,20,3,UnitInfo.ELITE_BERSERK,PlayerId.PLAYER_1)
        trigger.teleport_objects_in_area(0,0,20,3,0,10,PlayerId.PLAYER_1)
        




