from AoE2ScenarioParser.objects.support.new_effect import NewEffectSupport
from AoE2ScenarioParser.objects.data_objects.trigger import Trigger
from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.players import PlayerId


class TriggerManager:
    """
    Class to create triggers
    """

    def __init__(self, scenario: AoE2DEScenario) -> None:
        """
        Args:
            scenario (AoE2DEScenario): scenario to which the triggers will be added
        """
        self.scenario = scenario
        self.trigger_manager = scenario.trigger_manager

    def create_objects_in_area(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        object: UnitInfo,
        player_id: PlayerId,
        looping: bool = True,
    ):
        """
        Creates objects from the x1, y1, x2, y2 area
        """
        trigger = self.trigger_manager.add_trigger("Create Objects In Area")

        for i in range(x1, x2 + 1):
            for j in range(y1, y2 + 1):
                trigger.new_effect.create_object(
                    object_list_unit_id=object.ID,
                    source_player=player_id,
                    location_x=i,
                    location_y=j,
                )

        trigger.looping = looping

    def teleport_object_to_point(
        self,
        x: int,
        y: int,
        target_x: int,
        target_y: int,
        player_id: PlayerId,
        looping: bool = True,
    ):
        """
        Teleports object from the x, y point to the target_x, target_y point

        Args:
            x (int): x coordinate of the source point
            y (int): y coordinate of the source point
            target_x (int): x coordinate of the target point
            target_y (int): y coordinate of the target point
            player_id (PlayerId): player id of the object
            looping (bool, optional): if the trigger should loop. Defaults to True.
        """
        trigger = self.trigger_manager.add_trigger("Teleport Object To Point")

        trigger.new_effect.teleport_object(
            source_player=player_id,
            location_x=target_x,
            location_y=target_y,
            area_x1=x,
            area_y1=y,
            area_x2=x,
            area_y2=y,
        )

        trigger.looping = looping

    def teleport_objects_in_area(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        target_x: int,
        target_y: int,
        player_id: PlayerId,
        looping=True,
    ):
        """
        Teleports objects from the x1, y1, x2, y2 area to the target_x, target_y point

        Args:
            x1 (int): x1 coordinate of the source area
            y1 (int): y1 coordinate of the source area
            x2 (int): x2 coordinate of the source area
            y2 (int): y2 coordinate of the source area
            target_x (int): x coordinate of the target point
            target_y (int): y coordinate of the target point
            player_id (PlayerId): player id of the object
            looping (bool, optional): if the trigger should loop. Defaults to True.
        """
        trigger = self.trigger_manager.add_trigger("Teleport Objects In Area")

        trigger.new_effect.teleport_object(
            source_player=player_id,
            location_x=target_x,
            location_y=target_y,
            area_x1=x1,
            area_y1=y1,
            area_x2=x2,
            area_y2=y2,
        )

        trigger.looping = looping

    def teleport_objects_from_area_to_area(
        self,
        x11: int,
        y11: int,
        x21: int,
        y21: int,
        x12: int,
        y12: int,
        x22: int,
        y22: int,
        player_id: PlayerId,
        looping: bool = True,
    ):
        """
        Teleports objects from the x11, y11, x21, y21 area to the x12, y12, x22, y22 area

        Args:
            x11 (int): x11 coordinate of the source area
            y11 (int): y11 coordinate of the source area
            x21 (int): x21 coordinate of the source area
            y21 (int): y21 coordinate of the source area
            x12 (int): x12 coordinate of the target area
            y12 (int): y12 coordinate of the target area
            x22 (int): x22 coordinate of the target area
            y22 (int): y22 coordinate of the target area
            player_id (PlayerId): player id of the object
            looping (bool, optional): if the trigger should loop. Defaults to True."""
        trigger = self.trigger_manager.add_trigger("Teleport Objects From Area To Area")

        for i in range(x12, x22 + 1):
            for j in range(y12, y22 + 1):
                trigger.new_effect.teleport_object(
                    source_player=player_id,
                    location_x=i,
                    location_y=j,
                    area_x1=x11,
                    area_y1=y11,
                    area_x2=x21,
                    area_y2=y21,
                )

        trigger.looping = looping

    def spawn_infinite_waves(
        self,
        x11: int,
        y11: int,
        x21: int,
        y21: int,
        x12: int,
        y12: int,
        x22: int,
        y22: int,
        target_x: int,
        target_y: int,
        object: UnitInfo,
        player_id: PlayerId,
        looping: bool = True,
    ):
        """
        Spawns infinite waves of objects from the x11, y11, x21, y21 area to the x12, y12, x22, y22 area

        Args:
            x11 (int): x11 coordinate of the source area
            y11 (int): y11 coordinate of the source area
            x21 (int): x21 coordinate of the source area
            y21 (int): y21 coordinate of the source area
            x12 (int): x12 coordinate of the target area
            y12 (int): y12 coordinate of the target area
            x22 (int): x22 coordinate of the target area
            y22 (int): y22 coordinate of the target area
            object (UnitInfo): object to be spawned
            player_id (PlayerId): player id of the object
            looping (bool, optional): if the trigger should loop. Defaults to True.
        """
        spawn = self.trigger_manager.add_trigger("Spawn")
        teleport = self.trigger_manager.add_trigger("Teleport")
        attack_move = self.trigger_manager.add_trigger("Attack Move")
        timer = self.trigger_manager.add_trigger("Timer")

        spawn.enabled = True
        teleport.enabled = False
        attack_move.enabled = False
        timer.enabled = False

        # Spawn troops
        self.create_objects_in_area(x11, y11, x21, y21, object, player_id)
        spawn.new_effect.activate_trigger(trigger_id=teleport.ID)

        # Teleport troops to the target area
        for i in range(0, 1 + x12 - x11):
            for j in range(0, 1 + y12 - y11):
                # This teleports objects from the x1, y1 area to the x2, y2 area
                # The absolute values and modulo operations are used to make the objects stay within the target area
                teleport.new_effect.teleport_object(
                    source_player=player_id,
                    location_x=x21 + (i % (abs(x22 - x21))),
                    location_y=y21 + (j % (abs(y22 - y21))),
                    area_x1=x11 + i,
                    area_y1=y11 + j,
                    area_x2=x11 + i,
                    area_y2=y11 + j,
                )
        teleport.new_effect.activate_trigger(trigger_id=attack_move.ID)

        # Attack move to the target point
        attack_move.new_effect.attack_move(
            source_player=player_id,
            location_x=target_x,
            location_y=target_y,
            area_x1=x12,
            area_y1=y12,
            area_x2=x22,
            area_y2=y22,
        )

    def patrol(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        player_id: PlayerId,
        x_target: int,
        y_target: int,
        looping: bool = True,
    ):
        """
        Patrols objects from the x1, y1, x2, y2 area

        Args:
            x1 (int): x1 coordinate of the source area
            y1 (int): y1 coordinate of the source area
            x2 (int): x2 coordinate of the source area
            y2 (int): y2 coordinate of the source area
            player_id (PlayerId): player id of the object
            looping (bool, optional): if the trigger should loop. Defaults to True.
        """
        trigger = self.trigger_manager.add_trigger("Patrol")

        trigger.new_effect.patrol(
            area_x1=x1,
            area_y1=y1,
            area_x2=x2,
            area_y2=y2,
            source_player=player_id,
            location_x=x_target,
            location_y=y_target,
        )

        trigger.looping = looping
