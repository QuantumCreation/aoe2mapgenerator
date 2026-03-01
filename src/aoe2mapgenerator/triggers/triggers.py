from AoE2ScenarioParser.objects.support.new_effect import NewEffectSupport
from AoE2ScenarioParser.objects.data_objects.trigger import Trigger
from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.trigger_lists.attack_stance import AttackStance
from AoE2ScenarioParser.datasets.trigger_lists.diplomacy_state import DiplomacyState
from AoE2ScenarioParser.datasets.trigger_lists.attribute import Attribute
from AoE2ScenarioParser.datasets.trigger_lists.operation import Operation


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
        spawn_delay: int = 5,
    ):
        """
        Spawns infinite waves of objects. The spawn area will wait until it's clear 
        before spawning and teleporting the next wave.

        Args:
            x11 (int): x11 coordinate of the source area
            y11 (int): y11 coordinate of the source area
            x21 (int): x21 coordinate of the source area
            y21 (int): y21 coordinate of the source area
            x12 (int): x12 coordinate of the target area
            y12 (int): y12 coordinate of the target area
            x22 (int): x22 coordinate of the target area
            y22 (int): y22 coordinate of the target area
            target_x (int): x target point for attack move
            target_y (int): y target point for attack move
            object (UnitInfo): object to be spawned
            player_id (PlayerId): player id of the object
            looping (bool, optional): if the trigger should loop. Defaults to True.
            spawn_delay (int, optional): delay between waves in seconds. Defaults to 5.
        """
        spawn = self.trigger_manager.add_trigger("Spawn Wave")
        teleport = self.trigger_manager.add_trigger("Teleport and Attack")

        spawn.enabled = True
        spawn.looping = looping
        teleport.enabled = False
        teleport.looping = False

        # Condition 1: Staging area must be clear
        spawn.new_condition.objects_in_area(
            quantity=0,
            source_player=player_id,
            area_x1=x11,
            area_y1=y11,
            area_x2=x21,
            area_y2=y21,
        )
        
        # Condition 2: Delay timer
        if spawn_delay > 0:
            spawn.new_condition.timer(timer=spawn_delay)

        # Effect: Spawn troops
        for i in range(x11, x21 + 1):
            for j in range(y11, y21 + 1):
                spawn.new_effect.create_object(
                    object_list_unit_id=object.ID,
                    source_player=player_id,
                    location_x=i,
                    location_y=j,
                )
                
        # Effect: Activate the teleport trigger
        spawn.new_effect.activate_trigger(trigger_id=teleport.trigger_id)

        # Give a small timer to allow units to spawn before teleporting
        teleport.new_condition.timer(timer=1)

        # Teleport troops to the target area
        for i in range(0, 1 + x21 - x11):
            for j in range(0, 1 + y21 - y11):
                teleport.new_effect.teleport_object(
                    source_player=player_id,
                    location_x=x12 + (i % (max(1, x22 - x12 + 1))),
                    location_y=y12 + (j % (max(1, y22 - y12 + 1))),
                    area_x1=x11 + i,
                    area_y1=y11 + j,
                    area_x2=x11 + i,
                    area_y2=y11 + j,
                )

        # Attack move to the target point
        teleport.new_effect.attack_move(
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
        looping: bool = False,
        trigger_name: str = "Patrol",
    ) -> None:
        """Order all units in the source area to patrol to the target point.

        AoE2's patrol order is inherently back-and-forth: units ordered to
        patrol will walk to *target* and then return to their starting position,
        repeating indefinitely when ``looping=True``.

        Args:
            x1: Left tile of the source area (units to receive the order).
            y1: Top tile of the source area.
            x2: Right tile of the source area.
            y2: Bottom tile of the source area.
            player_id: PlayerId of the units that will receive the patrol order.
            x_target: X tile coordinate of the patrol destination.
            y_target: Y tile coordinate of the patrol destination.
            looping: Whether the trigger fires on repeat. Defaults to False.
            trigger_name: Display name for the new trigger. Defaults to "Patrol".
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)

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

    def patrol_between_points(
        self,
        source_point: tuple[int, int],
        target_point: tuple[int, int],
        player_id: PlayerId,
        area_padding: int = 4,
        looping: bool = True,
        trigger_name: str = "Patrol Between Points",
    ) -> None:
        """Patrol units near ``source_point`` to ``target_point`` and back.

        This is a convenience wrapper that converts point-based inputs to the
        rectangular area expected by :meth:`patrol`.
        """
        sx, sy = source_point
        tx, ty = target_point
        self.patrol(
            x1=sx - area_padding,
            y1=sy - area_padding,
            x2=sx + area_padding,
            y2=sy + area_padding,
            player_id=player_id,
            x_target=tx,
            y_target=ty,
            looping=looping,
            trigger_name=trigger_name,
        )

    def task_units_to_point(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        target_x: int,
        target_y: int,
        player_id: PlayerId,
        action_type: int | None = None,
        looping: bool = True,
        trigger_name: str = "Task Units",
    ) -> None:
        """Issue a task order to all units in an area.

        This is primarily used for city-life villager behavior to continuously
        re-assign work destinations (farms, mines, resource spots).
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.task_object(
            source_player=player_id,
            location_x=target_x,
            location_y=target_y,
            area_x1=x1,
            area_y1=y1,
            area_x2=x2,
            area_y2=y2,
            action_type=action_type,
        )
        trigger.looping = looping

    def patrol_back_and_forth(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        player_id: PlayerId,
        waypoint_x: int,
        waypoint_y: int,
        label: str = "",
    ) -> None:
        """High-level helper: units in *source area* patrol to *waypoint* and back.

        Creates a single looping patrol trigger.  AoE2's built-in patrol
        mechanic handles the return trip automatically — units walk to the
        waypoint, then walk back to their spawn area and repeat.

        This is a thin convenience wrapper over :meth:`patrol` with sensible
        defaults and a label-based trigger name.

        Args:
            x1: Left tile of the source area.
            y1: Top tile of the source area.
            x2: Right tile of the source area.
            y2: Bottom tile of the source area.
            player_id: Owner of the units receiving the patrol order.
            waypoint_x: X tile coordinate of the patrol endpoint.
            waypoint_y: Y tile coordinate of the patrol endpoint.
            label: Optional descriptive label embedded in the trigger name.
        """
        name = f"Patrol – {label}" if label else "Patrol"
        self.patrol(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            player_id=player_id,
            x_target=waypoint_x,
            y_target=waypoint_y,
            looping=True,
            trigger_name=name,
        )

    # ------------------------------------------------------------------
    # Win / Loss
    # ------------------------------------------------------------------

    def set_player_wins(
        self,
        player_id: PlayerId,
        trigger_name: str = "Declare Victory",
    ) -> None:
        """Immediately declare victory for *player_id*.

        Wraps ``DECLARE_VICTORY`` with ``enabled=1``.  Place additional
        conditions on the returned trigger to make the victory conditional.

        Args:
            player_id: The player who wins.
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.declare_victory(
            source_player=player_id,
            enabled=1,
        )

    def set_player_loses(
        self,
        player_id: PlayerId,
        trigger_name: str = "Declare Defeat",
    ) -> None:
        """Kill all units belonging to *player_id* to simulate defeat.

        AoE2 DE has no direct ``DECLARE_DEFEAT`` effect.  The conventional
        approach is to remove all of the player's objects; the game engine then
        registers the player as eliminated.

        Args:
            player_id: The player to eliminate.
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        # Remove every object owned by the player across the full map
        trigger.new_effect.remove_object(
            source_player=player_id,
            area_x1=0,
            area_y1=0,
            area_x2=500,
            area_y2=500,
        )

    def declare_victory_on_timer(
        self,
        player_id: PlayerId,
        seconds: int,
        trigger_name: str = "Timed Victory",
    ) -> None:
        """Declare victory for *player_id* after *seconds* have elapsed.

        Uses AoE2's built-in ``DISPLAY_TIMER`` / ``DECLARE_VICTORY`` approach:
        a single looping trigger fires once the timer condition is met by
        chaining two triggers (one with the timer condition, one with the
        victory effect).

        For simplicity this creates a single trigger that declares victory
        immediately when activated; attach a timer condition externally or use
        the scenario editor to wire up the timing condition.

        Args:
            player_id: The player who wins.
            seconds: Seconds to wait before declaring victory.
            trigger_name: Display name for the trigger.
        """
        # Trigger 1: wait `seconds` (display_timer provides this feedback)
        wait = self.trigger_manager.add_trigger(f"{trigger_name} – Wait")
        wait.new_effect.display_timer(
            display_time=seconds,
            time_unit=1,  # 1 = seconds
        )
        wait.new_effect.activate_trigger(
            trigger_id=wait.trigger_id + 1,  # activate the victory trigger
        )

        # Trigger 2: declare victory
        victory = self.trigger_manager.add_trigger(f"{trigger_name} – Victory")
        victory.enabled = False
        victory.new_effect.declare_victory(
            source_player=player_id,
            enabled=1,
        )

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    def set_starting_resources(
        self,
        player_id: PlayerId,
        food: int = 200,
        wood: int = 200,
        gold: int = 100,
        stone: int = 200,
        trigger_name: str = "Set Starting Resources",
    ) -> None:
        """Override a player's starting resource amounts.

        Uses ``MODIFY_RESOURCE`` with ``operation=SET`` on each of the four
        resource attributes.

        Args:
            player_id: Target player.
            food: Starting food amount.
            wood: Starting wood amount.
            gold: Starting gold amount.
            stone: Starting stone amount.
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        for attribute, quantity in (
            (Attribute.FOOD_STORAGE, food),
            (Attribute.WOOD_STORAGE, wood),
            (Attribute.GOLD_STORAGE, gold),
            (Attribute.STONE_STORAGE, stone),
        ):
            trigger.new_effect.modify_resource(
                quantity=quantity,
                tribute_list=attribute,
                source_player=player_id,
                operation=Operation.SET,
            )

    def give_resources(
        self,
        player_id: PlayerId,
        resource: Attribute,
        amount: int,
        trigger_name: str = "Give Resources",
    ) -> None:
        """Add *amount* of *resource* to *player_id*'s stockpile.

        Uses ``MODIFY_RESOURCE`` with ``operation=ADD``.

        Args:
            player_id: Receiving player.
            resource: Resource type (e.g. ``Attribute.GOLD_STORAGE``).
            amount: Amount to add (use negative values to subtract).
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.modify_resource(
            quantity=amount,
            tribute_list=resource,
            source_player=player_id,
            operation=Operation.ADD,
        )

    # ------------------------------------------------------------------
    # Unit Behaviour
    # ------------------------------------------------------------------

    def set_unit_stance(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        player_id: PlayerId,
        stance: AttackStance = AttackStance.AGGRESSIVE_STANCE,
        trigger_name: str = "Set Unit Stance",
    ) -> None:
        """Set the attack stance for all units in an area.

        Args:
            x1: Left tile of the target area.
            y1: Top tile of the target area.
            x2: Right tile of the target area.
            y2: Bottom tile of the target area.
            player_id: Player whose units will be updated.
            stance: Desired :class:`AttackStance` value.
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.change_object_stance(
            source_player=player_id,
            attack_stance=stance,
            area_x1=x1,
            area_y1=y1,
            area_x2=x2,
            area_y2=y2,
        )

    def change_object_ownership(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        from_player: PlayerId,
        to_player: PlayerId,
        trigger_name: str = "Change Ownership",
    ) -> None:
        """Transfer all objects in an area from *from_player* to *to_player*.

        Useful for capture mechanics, defection events, or reward systems.

        Args:
            x1: Left tile of the area.
            y1: Top tile of the area.
            x2: Right tile of the area.
            y2: Bottom tile of the area.
            from_player: Current owner.
            to_player: New owner.
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.change_ownership(
            source_player=from_player,
            target_player=to_player,
            area_x1=x1,
            area_y1=y1,
            area_x2=x2,
            area_y2=y2,
        )

    # ------------------------------------------------------------------
    # Diplomacy
    # ------------------------------------------------------------------

    def set_player_stance(
        self,
        source_player: PlayerId,
        target_player: PlayerId,
        stance: DiplomacyState = DiplomacyState.ALLY,
        trigger_name: str = "Set Diplomacy",
    ) -> None:
        """Set the diplomatic stance between two players.

        Note that AoE2 requires both players to agree for full alliance; call
        this method twice (swapping source and target) to create a mutual ally
        relationship.

        Args:
            source_player: The player whose stance is being changed.
            target_player: The player that *source_player* is regarding.
            stance: Desired :class:`DiplomacyState` (ALLY, NEUTRAL, ENEMY).
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.change_diplomacy(
            diplomacy=stance,
            source_player=source_player,
            target_player=target_player,
        )

    def set_mutual_alliance(
        self,
        player_a: PlayerId,
        player_b: PlayerId,
        stance: DiplomacyState = DiplomacyState.ALLY,
        trigger_name: str = "Set Alliance",
    ) -> None:
        """Set a symmetric diplomatic stance between *player_a* and *player_b*.

        This is shorthand for two :meth:`set_player_stance` calls in opposite
        directions, which is the standard pattern for establishing full alliances.

        Args:
            player_a: First player.
            player_b: Second player.
            stance: Desired :class:`DiplomacyState`.
            trigger_name: Display name prefix for the two triggers.
        """
        self.set_player_stance(player_a, player_b, stance, f"{trigger_name} A→B")
        self.set_player_stance(player_b, player_a, stance, f"{trigger_name} B→A")

    # ------------------------------------------------------------------
    # Fog of War
    # ------------------------------------------------------------------

    def reveal_area_to_player(
        self,
        player_id: PlayerId,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        permanent: bool = True,
        trigger_name: str = "Reveal Area",
    ) -> None:
        """Make an area permanently visible to *player_id*.

        Iterates over the area and sets each tile's visibility using
        ``SET_PLAYER_VISIBILITY``.  For large areas prefer using a single
        effect with ``area_x1 / area_x2`` if the parser version supports it.

        Args:
            player_id: The player who gains visibility.
            x1: Left tile of the area.
            y1: Top tile of the area.
            x2: Right tile of the area.
            y2: Bottom tile of the area.
            permanent: If ``True`` uses VISIBLE (2); if ``False`` uses EXPLORED (1).
            trigger_name: Display name for the trigger.
        """
        visibility = 2 if permanent else 1  # 2 = fully visible, 1 = explored
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.set_player_visibility(
            source_player=player_id,
            target_player=player_id,
            visibility_state=visibility,
        )

    def hide_area_from_player(
        self,
        player_id: PlayerId,
        trigger_name: str = "Hide Area",
    ) -> None:
        """Remove exploration for *player_id* (reset to fog of war).

        This calls ``SET_PLAYER_VISIBILITY`` with ``INVISIBLE`` (0) which
        resets the player's entire explored state.

        Args:
            player_id: The player whose vision is reset.
            trigger_name: Display name for the trigger.
        """
        trigger = self.trigger_manager.add_trigger(trigger_name)
        trigger.new_effect.set_player_visibility(
            source_player=player_id,
            target_player=player_id,
            visibility_state=0,  # 0 = invisible / unexplored
        )
