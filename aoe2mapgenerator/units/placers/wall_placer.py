"""
WallPlacer class for placing walls on a map.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.point_manager import PointManager
from aoe2mapgenerator.common.constants.constants import DEFAULT_PLAYER
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.common.enums.enum import AOE2ObjectType
from aoe2mapgenerator.units.placers.placer_configs import AddBordersConfig


class WallPlacer(PlacerBase):
    """
    Class for placing walls on a map.
    """

    # ****************************************************************************************
    # Doesn't correctly account for objects with a size greater than 1
    def add_borders(
        self,
        configuration: AddBordersConfig,
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
        point_manager = configuration.point_manager
        map_layer_type = configuration.map_layer_type
        obj_type = configuration.obj_type
        player_id = configuration.player_id
        margin = configuration.margin

        if player_id is None:
            player_id = DEFAULT_PLAYER

        points = point_manager.get_point_list_copy()

        # As points are added to the original point manager
        # They get removed, howeer that interferes with the loop
        # that calculates whether or not a point is on the border.
        copy_of_original_manager = point_manager.copy()

        for point in points:
            if self._is_on_border(copy_of_original_manager, point, margin):

                self.safe_set_point(
                    point_manager=point_manager,
                    point=point,
                    obj_type=obj_type,
                    map_layer_type=map_layer_type,
                    player_id=player_id,
                )

        return

    def _is_on_border(
        self,
        point_manager: PointManager,
        point: tuple[int, int],
        margin: int,
    ):
        """
        Checks if given point is on a border.

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
            margin: Number of squares to fill in along the edge.
        """
        x, y = point

        for i in range(-margin, margin + 1):
            for j in range(-abs(abs(i) - margin), abs(abs(i) - margin) + 1):
                neighbor_point = (x + i, y + j)
                print(neighbor_point)
                point_exists = point_manager.check_point_exists(neighbor_point)
                if not point_exists:
                    print("Point Doesn't Exist")
                    return True

        return False
