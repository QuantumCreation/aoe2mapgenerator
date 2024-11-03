"""
TODO: 
"""

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo

from aoe2mapgenerator.src.common.enums.enum import (
    Directions,
    MapLayerType,
    GateType,
    CheckPlacementReturnTypes,
)
from aoe2mapgenerator.src.units.placers.point_manager import PointManager
from aoe2mapgenerator.src.common.constants.constants import DEFAULT_PLAYER
from aoe2mapgenerator.src.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.src.map.map_object import AOE2ObjectType
from aoe2mapgenerator.src.common.enums.enum import GateObject
from aoe2mapgenerator.src.common.constants.constants import (
    GHOST_OBJECT_DISPLACEMENT_ID,
)
from aoe2mapgenerator.src.units.utils import manhattan_distance


class GatePlacer(PlacerBase):
    """
    Class for placing gates on a map.
    """

    def place_gate_on_four_sides(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        gate_type: GateType,
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

        if len(point_manager.get_point_list()) == 0:
            return

        avg_point = self._get_average_point_position(point_manager)

        for direction in [
            Directions.EAST,
            Directions.WEST,
            Directions.NORTH,
            Directions.SOUTH,
        ]:

            point = self._get_first_point_in_given_direction(
                point_manager, avg_point, direction
            )

            if point is None:
                continue

            self._place_gate_closest_to_point(
                point_manager=point_manager,
                map_layer_type=map_layer_type,
                gate_type=gate_type,
                goal_placement_point=point,
                player_id=player_id,
            )

    def place_gate_on_eight_sides(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        gate_type: GateType,
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

        if len(point_manager.get_point_list()) == 0:
            return

        avg_point = self._get_average_point_position(point_manager)

        for direction in [
            Directions.NORTH,
            Directions.SOUTH,
            Directions.EAST,
            Directions.WEST,
            Directions.NORTHEAST,
            Directions.NORTHWEST,
            Directions.SOUTHEAST,
            Directions.SOUTHWEST,
        ]:

            point = self._get_first_point_in_given_direction(
                point_manager, avg_point, direction
            )

            if point is None:
                continue

            self._place_gate_closest_to_point(
                point_manager=point_manager,
                map_layer_type=map_layer_type,
                gate_type=gate_type,
                goal_placement_point=point,
                player_id=player_id,
            )

    # --------------------------- GATE HELPER METHODS ---------------------------------

    def _get_gate_objects(self, gate_type: GateType) -> list[GateObject]:
        """
        Gets the object type for the gate.
        """
        return GateType.get_gate_objects_from_gate_type(gate_type)

    def _place_gate_closest_to_point(
        self,
        point_manager: PointManager,
        map_layer_type: MapLayerType,
        gate_type: GateType,
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
            key=lambda point: manhattan_distance(point, goal_placement_point),
        ):
            for gate_object in gate_objects:
                status = self._check_placement_for_gate(
                    point_manager, gate_object, (x, y)
                )

                if status == CheckPlacementReturnTypes.FAIL:
                    continue

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

        iteration_point = starting_point

        # NOTE THIS CAN BE OPTIMIZED BY STARTING AT THE GIVEN POINT AND NOT GOING BEYOND MAP BOUNDARIES
        # IT CURRENTLY RUNS THE FULL LENGTH OF THE MAP NO MATTER WHAT.
        for i in range(self.map.size):

            if not points_manager.check_point_exists(iteration_point):
                direction_tuple = direction.value
                iteration_point = (
                    iteration_point[0] + direction_tuple[0],
                    iteration_point[1] + direction_tuple[1],
                )
            else:
                return iteration_point

        return None

    def _check_placement_for_gate(
        self,
        point_manager: PointManager,
        gate_object: GateObject,
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
        gate_object: GateObject,
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

        gate_dimensions = GateObject.get_gate_dimensions(gate_object)
        points_to_place = [
            (point_to_place[0] + x, point_to_place[1] + y) for x, y in gate_dimensions
        ]

        for i, point in enumerate(points_to_place):
            aoe2_object: AOE2ObjectType = BuildingInfo[gate_object.value]

            if i == 2:
                self.map.set_point(point, aoe2_object, map_layer_type, player_id)
            else:
                self.map.set_point(
                    point,
                    GHOST_OBJECT_DISPLACEMENT_ID,
                    map_layer_type,
                    player_id,
                )

            point_manager.remove_point(point_to_place)
            self.points_set_on_map += 1
