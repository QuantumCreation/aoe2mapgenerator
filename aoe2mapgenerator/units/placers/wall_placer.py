"""
TODO: Add description.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import DEFAULT_PLAYER
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType


class WallPlacer(PlacerBase):
    """
    Class for placing walls on a map.
    """

    # Multiple map type Callableality still seems a bit weird to me. May refactor later.
    def add_borders(
        self,
        points_manager: PointManager,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        player_id: PlayerId = DEFAULT_PLAYER,
        margin: int = 1,
    ):
        """
        Adds borders to a cell based on border margin size and type.

        Args:
            map_layer_type: The map type.
            array_space_type: Array space id to get points for.
            obj_type_list: The type of object to be placed.
            margin: Type of margin to place.
            player_id: Id of the objects being placed.
            place_on_n_maps: Number of maps to place the objects on.
        """
        if player_id is None:
            player_id = DEFAULT_PLAYER

        points = points_manager.get_point_list()

        for point in points:
            if self._is_on_border(points_manager, point, margin):
                x, y = point
                self.map.set_point(x, y, obj_type, map_layer_type, player_id)

        return

    def _is_on_border(
        self, point_manager: PointManager, point: tuple[int, int], margin
    ):
        """
        Checks if given point is on a border.

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
            margin: Number of squares to fill in along the edge.
        """
        x, y = point
        points_list = point_manager.get_point_list()

        for i in range(-margin, margin + 1):
            for j in range(-abs(abs(i) - margin), abs(abs(i) - margin) + 1):
                if not (x + i, y + j) in points_list:
                    return True

        return False
