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
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.map.map_object import AOE2ObjectType
from aoe2mapgenerator.common.enums.enum import GateObjects
from aoe2mapgenerator.common.constants.constants import (
    DEFAULT_EMPTY_VALUE,
    GHOST_OBJECT_DISPLACEMENT_ID,
)


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

    def list_to_tuple(self, lst: list) -> tuple:
        """
        Converts a list to a tuple.
        """
        if isinstance(lst, list) and len(lst) == 2:
            return tuple(lst)

        return lst

    # --------------------------- GATE HELPER METHODS ---------------------------------

    def _get_gate_objects(self, gate_type: GateTypes) -> list[GateObjects]:
        """
        Gets the object type for the gate.
        """
        return GateObjects.get_gate_names_from_gate_type(gate_type)

    def _place_gate_closest_to_point(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        gate_type: GateTypes,
        goal_placement_point: tuple,
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

        points = point_manager.get_point_list()

        gate_objects = self._get_gate_objects(gate_type)

        for x, y in sorted(
            points,
            key=lambda point: self._manhattan_distance(point, goal_placement_point),
        ):
            for gate_object in gate_objects:
                status = self._check_placement_for_gate(
                    point_manager, gate_object, goal_placement_point
                )
                if status == CheckPlacementReturnTypes.FAIL:
                    pass

                if status == CheckPlacementReturnTypes.SUCCESS:
                    self._place_gate(
                        point_manager, map_layer_type, (x, y), gate_object, player_id
                    )
                    return

    def _get_average_point_position(self, point_manager: PointManager):
        """
        Gets the location of the average point from the given value type and array space lists.
        """
        total_points = 0
        totx = 0
        toty = 0

        smallest_set = point_manager.get_point_list()

        for point in smallest_set:
            status = self._check_placement(point_manager, point, None, 0)

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

    def _check_placement_for_gate(
        self,
        point_manager: PointManager,
        gate_object: GateObjects,
        goal_placement_point: tuple,
    ):
        """
        Checks if the given point is a valid placement for a gate.

        Args:
            point_manager: The point manager.
            goal_placement_point: The point to place the object.
            obj_type: The type of object to be placed.
            margin: The margin around the object.
        """

        points_to_check = gate_object.get_gate_dimensions()

        for point in points_to_check:
            goal_x, goal_y = goal_placement_point
            x, y = point
            x_actual, y_actual = x + goal_x, y + goal_y
            point = (x_actual, y_actual)

            if not point_manager.check_point_exists(point):
                return CheckPlacementReturnTypes.FAIL

        return CheckPlacementReturnTypes.SUCCESS

    def _place_gate(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        point_to_place: tuple[int, int],
        gate_type: GateTypes,
        player_id: PlayerId,
    ):
        """
        Places a gate on the map.

        Args:
            points_manager: The point manager.
            map_layer_type: The map type.
            gate_type: The type of gate being placed.
            player_id: Id of the objects being placed.
        """

        gate_dimensions = GateObjects.get_gate_dimensions(gate_type)
        points_to_place = [
            (point_to_place[0] + x, point_to_place[1] + y) for x, y in gate_dimensions
        ]

        for i, point in enumerate(points_to_place):
            if i == 1:
                self.map.set_point(
                    point[0], point[1], gate_type, map_layer_type, player_id
                )
            else:
                self.map.set_point(
                    point[0],
                    point[1],
                    GHOST_OBJECT_DISPLACEMENT_ID,
                    map_layer_type,
                    player_id,
                )

            point_manager.remove_point(point_to_place)
            self.points_set_on_map += 1
