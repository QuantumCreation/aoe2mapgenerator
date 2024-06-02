import random
from re import A
from site import abs_paths
from telnetlib import GA
from typing import Union, Callable

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
import functools

from aoe2mapgenerator.common.enums.enum import ObjectSize, Directions, MapLayerType, GateTypes, CheckPlacementReturnTypes
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import GHOST_OBJECT_DISPLACEMENT, DEFAULT_OBJECT_TYPES, GHOST_OBJECT_MARGIN, DEFAULT_PLAYER
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.placer_base import PlacerBase


class GatePlacer(PlacerBase):

    def __init__(self, map: Map):
        super().__init__(map)

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
            point = self._get_first_point_in_given_direction(points_manager, avg_point, direction)

            if point is None:
                print(f"No point found in the {direction} direction.")
                continue

            self._place_gate_closest_to_point(points_manager, map_layer_type, gate_type, point, player_id)

    def list_to_tuple(self, lst):
        if isinstance(lst, list) and len(lst) == 2:
            return tuple(lst)
        else:
            return lst
    # --------------------------- GATE HELPER METHODS ---------------------------------

    def _get_average_point_position(
            self,
            points_manager: PointManager
            ):
        """
        Gets the location of the average point from the given value type and array space lists.
        """
        total_points = 0
        totx = 0
        toty = 0

        smallest_set = points_manager.get_point_list()

        for point in smallest_set:
            status = self._check_placement(points_manager, point, None,0,width=1,height=1)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return (0,0)

            if status == CheckPlacementReturnTypes.SUCCESS:
                total_points += 1
                totx += point[0]
                toty += point[1]

        return (totx//total_points, toty//total_points)
    
    def _get_first_point_in_given_direction(
        self, 
        points_manager: PointManager,
        starting_point: tuple,
        direction: Directions
        ):
        """
        Finds the first point in the matching array space type with the given direction.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            starting_point: Point to start searching from.
            direciton: Direction to search in.
        """
        starting_point = starting_point

        points = points_manager.get_point_list()

        # NOTE THIS CAN BE OPTIMIZED BY STARTING AT THE GIVEN POINT AND NOT GOING BEYOND MAP BOUNDARIES
        # IT CURRENTLY RUNS THE FULL LENGTH OF THE MAP NO MATTER WHAT.
        for i in range(self.map.size):

            if starting_point in points:
                status = self._check_placement(points_manager, starting_point, None, 0, width = 1, height = 1)

                if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                    return None

                if status == CheckPlacementReturnTypes.SUCCESS:
                    return starting_point

            next_point = tuple(map(sum, zip(starting_point, direction)))
            starting_point = next_point
        
        return None

    # Maybe this and the other place method could be joined or simplified somehow.
    def _place_gate_closest_to_point(
        self, 
        points_manager: PointManager,
        map_layer_type: MapLayerType, 
        gate_type: GateTypes, 
        starting_point, 
        player_id: PlayerId,
        ):
        """
        Places a gate as close as possible to the starting point.
        """
        points_set = points_manager.get_point_list()

        for (x,y) in sorted(points_set, key = lambda point: ((point[0]-starting_point[0])**2 + (point[1]-starting_point[1])**2)):

            status = self._check_placement(points_manager, (x,y), None, margin = 0, width = 1, height = 4)
            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return

            if status == CheckPlacementReturnTypes.SUCCESS:
                obj_type = BuildingInfo[gate_type.value[2]]
                self._place(map_layer_type, (x,y), obj_type, player_id, margin=0, ghost_margin=0, width = 1, height = 4)
                return

            status = self._check_placement(points_manager, (x,y), None, margin = 0, width = 4, height = 1)

            if status == CheckPlacementReturnTypes.SUCCESS_IMPOSSIBLE:
                return

            if status == CheckPlacementReturnTypes.SUCCESS:
                try:
                    obj_type = BuildingInfo[gate_type.value[3]]
                except:
                    print(gate_type)
                    raise ValueError("Invalid gate type.")
                self._place(map_layer_type, (x,y), obj_type, player_id, margin=0, ghost_margin=0, width = 4, height = 1)
                return
        
        return



