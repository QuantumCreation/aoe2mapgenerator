"""
TODO: 
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo

from aoe2mapgenerator.common.enums.enum import (
    Directions,
    MapLayerType,
    GateTypes,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import DEFAULT_PLAYER
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.map.map_object import AOE2ObjectType


class GatePlacer(PlacerBase):
    """
    Class for placing gates on a map.
    """

    def place_gate_on_four_sides(
        self,
        points_manager: PointManager,
        map_layer_type: MapLayerType,
        gate_type: GateTypes,
        player_id: PlayerId = DEFAULT_PLAYER,
    ):
        """
        Takes the average location of points in the given array space, and places gates on four sides.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            gate_type: Type of the gate being placed
            playerId: Id of the objects being placed.
        """

        avg_point = self._get_average_point_position(points_manager)

        for direction in [direction.value for direction in Directions]:
            point = self._get_first_point_in_given_direction(
                points_manager, avg_point, direction
            )

            if point is None:
                print(f"No point found in the {direction} direction.")
                continue

            self._place_gate_closest_to_point(
                points_manager, map_layer_type, gate_type, point, player_id
            )

    def list_to_tuple(self, lst: list) -> tuple:
        """
        Converts a list to a tuple.
        """
        if isinstance(lst, list) and len(lst) == 2:
            return tuple(lst)

        return lst

    # --------------------------- GATE HELPER METHODS ---------------------------------

    def _get_gate_objects(
        self, gate_type: GateTypes, player_id: PlayerId = DEFAULT_PLAYER
    ) -> list[AOE2ObjectType]:
        """
        Gets the object type for the gate.
        """

    def _place_gate_closest_to_point(
        self,
        points_manager: PointManager,
        map_layer_type: MapLayerType,
        gate_type: GateTypes,
        starting_point: tuple,
        player_id: PlayerId,
    ):
        """
        Places a gate as close as possible to the starting point.

        Args:
            points_manager: The point manager.
            map_layer_type: The map type.
            gate_type: The type of gate to be placed.
            starting_point: The point to place the gate.
            player_id: Id of the player for the given gate.
        """

        points = points_manager.get_point_list()

        for x, y in sorted(
            points,
            key=lambda point: self._manhattan_distance(point, starting_point),
        ):

            status = self._check_placement(points_manager, (x, y), gate_type, 0)
            if status == CheckPlacementReturnTypes.FAIL:
                return

            gate_type = GateTypes(gate_type)
            self._place(
                points_manager,
                map_layer_type,
                (x, y),
                gate_type,
                player_id,
                0,
            )

    def _get_average_point_position(self, points_manager: PointManager):
        """
        Gets the location of the average point from the given value type and array space lists.
        """
        total_points = 0
        totx = 0
        toty = 0

        smallest_set = points_manager.get_point_list()

        for point in smallest_set:
            status = self._check_placement(points_manager, point, None, 0)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return (0, 0)

            if status == CheckPlacementReturnTypes.SUCCESS:
                total_points += 1
                totx += point[0]
                toty += point[1]

        return (totx // total_points, toty // total_points)

    def _get_first_point_in_given_direction(
        self, points_manager: PointManager, starting_point: tuple, direction: Directions
    ):
        """
        Finds the first point in the matching array space type with the given direction.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            starting_point: Point to start searching from.
            direciton: Direction to search in.
        """
        points = points_manager.get_point_list()

        # NOTE THIS CAN BE OPTIMIZED BY STARTING AT THE GIVEN POINT AND NOT GOING BEYOND MAP BOUNDARIES
        # IT CURRENTLY RUNS THE FULL LENGTH OF THE MAP NO MATTER WHAT.
        for i in range(self.map.size):

            if starting_point in points:
                # Need to add actual values for gate width and height
                status = self._check_placement(points_manager, starting_point, None, 0)

                if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                    return None

                if status == CheckPlacementReturnTypes.SUCCESS:
                    return starting_point

            next_point = tuple(map(sum, zip(starting_point, direction)))
            starting_point = next_point

        return None
