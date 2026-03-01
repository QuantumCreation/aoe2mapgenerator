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
