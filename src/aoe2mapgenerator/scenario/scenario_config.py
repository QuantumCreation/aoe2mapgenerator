"""ScenarioConfig and PlayerConfig — high-level scenario configuration.

These dataclasses centralise every per-scenario and per-player configuration
option into a single, validated structure that can be applied to an
``AoE2DEScenario`` via :func:`configure_scenario`.

Typical usage::

    from aoe2mapgenerator.scenario.scenario_config import (
        PlayerConfig,
        ScenarioConfig,
        configure_scenario,
    )
    from AoE2ScenarioParser.datasets.object_support import Civilization, StartingAge
    from AoE2ScenarioParser.datasets.players import PlayerId
    from AoE2ScenarioParser.datasets.trigger_lists.diplomacy_state import DiplomacyState

    config = ScenarioConfig(
        map_name="Battle of the Plains",
        players=[
            PlayerConfig(
                player_id=PlayerId.ONE,
                name="Knights of the North",
                civilization=Civilization.FRANKS,
                starting_age=StartingAge.FEUDAL_AGE,
                starting_food=500,
                starting_wood=300,
                starting_gold=200,
                starting_stone=100,
            ),
            PlayerConfig(
                player_id=PlayerId.TWO,
                name="Empire of the East",
                civilization=Civilization.CHINESE,
                starting_age=StartingAge.DARK_AGE,
            ),
        ],
        allied_pairs=[(PlayerId.ONE, PlayerId.THREE)],
        enemy_pairs=[(PlayerId.ONE, PlayerId.TWO)],
    )

    configure_scenario(scenario, config)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from AoE2ScenarioParser.datasets.object_support import Civilization, StartingAge
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.trigger_lists.diplomacy_state import DiplomacyState
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario


@dataclass
class PlayerConfig:
    """Configuration for a single player slot.

    Attributes:
        player_id: AoE2 player slot (ONE through EIGHT).  GAIA is not supported.
        name: In-game tribe / player name displayed during the scenario.
        civilization: Civilization enum value or raw integer (0 = Random).
        starting_age: Age the player begins in.  Defaults to Dark Age.
        starting_food: Starting food amount.
        starting_wood: Starting wood amount.
        starting_gold: Starting gold amount.
        starting_stone: Starting stone amount.
        population_cap: Maximum unit population (default 200).
        allied_victory: Whether allied victory is enabled for this player.
        active: Whether this player slot is active / seated.
    """

    player_id: PlayerId
    name: str = ""
    civilization: int | Civilization = 0  # 0 = Random civilization
    starting_age: StartingAge = StartingAge.DARK_AGE
    starting_food: int = 200
    starting_wood: int = 200
    starting_gold: int = 100
    starting_stone: int = 200
    population_cap: int = 200
    allied_victory: bool = False
    active: bool = True

    def __post_init__(self) -> None:
        if self.player_id == PlayerId.GAIA:
            raise ValueError("PlayerConfig does not support GAIA (player 0).")
        for attr, value in (
            ("starting_food", self.starting_food),
            ("starting_wood", self.starting_wood),
            ("starting_gold", self.starting_gold),
            ("starting_stone", self.starting_stone),
            ("population_cap", self.population_cap),
        ):
            if value < 0:
                raise ValueError(f"PlayerConfig.{attr} must be >= 0, got {value}.")


@dataclass
class ScenarioConfig:
    """Top-level scenario configuration applied to an ``AoE2DEScenario``.

    Attributes:
        map_name: Title of the scenario (shown in the lobby and loading screen).
        instructions: Objective / hint text displayed at scenario start.
        players: Per-player configurations.  Players not listed here are left
            untouched from the base scenario defaults.
        allied_pairs: Pairs of player IDs that should be set as allies.
            This sets diplomacy *both ways* (mutual alliance).
        enemy_pairs: Pairs of player IDs that should be set as enemies.
            This sets diplomacy *both ways* (mutual hostility).
        neutral_pairs: Pairs of player IDs that should be set as neutral.
    """

    map_name: str = "Generated Map"
    instructions: str = ""
    players: List[PlayerConfig] = field(default_factory=list)
    allied_pairs: List[Tuple[PlayerId, PlayerId]] = field(default_factory=list)
    enemy_pairs: List[Tuple[PlayerId, PlayerId]] = field(default_factory=list)
    neutral_pairs: List[Tuple[PlayerId, PlayerId]] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Deduplicate player slots
        seen: set[PlayerId] = set()
        for pc in self.players:
            if pc.player_id in seen:
                raise ValueError(
                    f"Duplicate PlayerConfig for player_id={pc.player_id}."
                )
            seen.add(pc.player_id)


def configure_scenario(scenario: AoE2DEScenario, config: ScenarioConfig) -> None:
    """Apply *config* to *scenario* in-place.

    This function mutates the ``AoE2DEScenario`` player data directly.  Call
    :meth:`AoE2DEScenario.write_to_file` after calling this function to persist
    the changes to disk.

    Args:
        scenario: Live ``AoE2DEScenario`` object to configure.
        config: :class:`ScenarioConfig` describing the desired outcome.

    Raises:
        KeyError: If a ``PlayerConfig.player_id`` references a slot not present
            in the scenario's player manager.
    """
    pm = scenario.player_manager

    # ------------------------------------------------------------------
    # Per-player settings
    # ------------------------------------------------------------------
    for pc in config.players:
        player = pm.players[pc.player_id]

        if pc.name:
            player.tribe_name = pc.name

        player.civilization = pc.civilization
        player.starting_age = pc.starting_age
        player.food = pc.starting_food
        player.wood = pc.starting_wood
        player.gold = pc.starting_gold
        player.stone = pc.starting_stone

        if player.population_cap is not None:
            player.population_cap = pc.population_cap

        if player.allied_victory is not None:
            player.allied_victory = pc.allied_victory

    # ------------------------------------------------------------------
    # Diplomacy
    # ------------------------------------------------------------------
    for player_a_id, player_b_id in config.allied_pairs:
        pm.players[player_a_id].set_player_diplomacy(player_b_id, DiplomacyState.ALLY)
        pm.players[player_b_id].set_player_diplomacy(player_a_id, DiplomacyState.ALLY)

    for player_a_id, player_b_id in config.enemy_pairs:
        pm.players[player_a_id].set_player_diplomacy(player_b_id, DiplomacyState.ENEMY)
        pm.players[player_b_id].set_player_diplomacy(player_a_id, DiplomacyState.ENEMY)

    for player_a_id, player_b_id in config.neutral_pairs:
        pm.players[player_a_id].set_player_diplomacy(player_b_id, DiplomacyState.NEUTRAL)
        pm.players[player_b_id].set_player_diplomacy(player_a_id, DiplomacyState.NEUTRAL)
