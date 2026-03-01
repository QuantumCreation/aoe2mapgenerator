import pytest
from unittest.mock import MagicMock

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo

from aoe2mapgenerator.triggers.triggers import TriggerManager

def test_spawn_infinite_waves():
    scenario_mock = MagicMock(spec=AoE2DEScenario)
    
    tm = TriggerManager(scenario_mock)
    
    trigger_mock_1 = MagicMock()
    trigger_mock_1.trigger_id = 10
    trigger_mock_1.new_effect = MagicMock()
    trigger_mock_1.new_condition = MagicMock()
    
    trigger_mock_2 = MagicMock()
    trigger_mock_2.trigger_id = 11
    trigger_mock_2.new_effect = MagicMock()
    trigger_mock_2.new_condition = MagicMock()
    
    scenario_mock.trigger_manager.add_trigger.side_effect = [trigger_mock_1, trigger_mock_2]
    
    unit_mock = MagicMock(spec=UnitInfo)
    unit_mock.ID = 4
    
    tm.spawn_infinite_waves(
        x11=0, y11=0, x21=2, y21=2,
        x12=10, y12=10, x22=12, y22=12,
        target_x=20, target_y=20,
        object=unit_mock,
        player_id=1,
        spawn_delay=5
    )
    
    assert scenario_mock.trigger_manager.add_trigger.call_count == 2
    
    # Check that conditions were applied
    trigger_mock_1.new_condition.objects_in_area.assert_called_once()
    trigger_mock_1.new_condition.timer.assert_called_once_with(timer=5)
    
    # Check that spawn effect was called
    assert trigger_mock_1.new_effect.create_object.call_count == 9 # 3x3 grid
    
    # Check that teleport activate trigger was called
    trigger_mock_1.new_effect.activate_trigger.assert_called_once_with(trigger_id=11)
    
    # Check teleport
    assert trigger_mock_2.new_effect.teleport_object.call_count == 9 # 3x3 grid
    
    # Check attack move
    trigger_mock_2.new_effect.attack_move.assert_called_once()

def test_setup_dynamic_ambush():
    scenario_mock = MagicMock(spec=AoE2DEScenario)
    tm = TriggerManager(scenario_mock)
    
    trigger_mock = MagicMock()
    scenario_mock.trigger_manager.add_trigger.return_value = trigger_mock
    
    unit_mock = MagicMock(spec=UnitInfo)
    unit_mock.ID = 5
    
    tm.setup_dynamic_ambush(
        0, 0, 5, 5,
        10, 10, 12, 12,
        target_player_id=1,
        ambush_player_id=2,
        unit_to_spawn=unit_mock
    )
    
    scenario_mock.trigger_manager.add_trigger.assert_called_once_with("Dynamic Ambush")
    trigger_mock.new_condition.objects_in_area.assert_called_once()
    assert trigger_mock.new_effect.create_object.call_count == 9
    trigger_mock.new_effect.attack_move.assert_called_once()

def test_setup_capturable_outpost():
    scenario_mock = MagicMock(spec=AoE2DEScenario)
    tm = TriggerManager(scenario_mock)
    
    trigger_mock = MagicMock()
    scenario_mock.trigger_manager.add_trigger.return_value = trigger_mock
    
    tm.setup_capturable_outpost(0, 0, 2, 2, players_to_check=[1, 2])
    
    assert scenario_mock.trigger_manager.add_trigger.call_count == 2
    assert trigger_mock.new_condition.objects_in_area.call_count == 4
    assert trigger_mock.new_effect.change_ownership.call_count == 4

def test_setup_resource_trickle():
    from AoE2ScenarioParser.datasets.trigger_lists.attribute import Attribute
    scenario_mock = MagicMock(spec=AoE2DEScenario)
    tm = TriggerManager(scenario_mock)
    
    trigger_mock = MagicMock()
    scenario_mock.trigger_manager.add_trigger.return_value = trigger_mock
    
    tm.setup_resource_trickle(1, Attribute.GOLD_STORAGE, 100)
    
    scenario_mock.trigger_manager.add_trigger.assert_called_once_with("Resource Trickle")
    trigger_mock.new_condition.timer.assert_called_once_with(timer=10)
    trigger_mock.new_effect.modify_resource.assert_called_once()

def test_patrol_route():
    scenario_mock = MagicMock(spec=AoE2DEScenario)
    tm = TriggerManager(scenario_mock)
    
    trigger_mock_1 = MagicMock()
    trigger_mock_1.trigger_id = 1
    trigger_mock_2 = MagicMock()
    trigger_mock_2.trigger_id = 2
    
    scenario_mock.trigger_manager.add_trigger.side_effect = [trigger_mock_1, trigger_mock_2]
    
    tm.patrol_route(1, 0, 0, 2, 2, [(10, 10), (20, 20)])
    
    assert scenario_mock.trigger_manager.add_trigger.call_count == 2
    assert trigger_mock_1.new_condition.timer.call_count == 1
    trigger_mock_1.new_effect.task_object.assert_called_once()
    trigger_mock_1.new_effect.activate_trigger.assert_called_once_with(trigger_id=2)
    trigger_mock_1.new_effect.deactivate_trigger.assert_called_once_with(trigger_id=1)

def test_teleport_objects_from_area_to_area():
    scenario_mock = MagicMock(spec=AoE2DEScenario)
    tm = TriggerManager(scenario_mock)
    
    trigger_mock = MagicMock()
    scenario_mock.trigger_manager.add_trigger.return_value = trigger_mock
    
    tm.teleport_objects_from_area_to_area(
        0, 0, 2, 2, # 3x3 source area
        10, 10, 15, 15, # 6x6 target area
        player_id=1
    )
    
    scenario_mock.trigger_manager.add_trigger.assert_called_once_with("Teleport Objects From Area To Area")
    assert trigger_mock.new_effect.teleport_object.call_count == 9
