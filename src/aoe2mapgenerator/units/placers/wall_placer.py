"""
WallPlacer class for placing walls on a map.
"""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.common.constants.constants import DEFAULT_PLAYER
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.common.types import AOE2ObjectType
from aoe2mapgenerator.units.placers.placer_configs import AddBordersConfig
from aoe2mapgenerator.units.placers.placer_configs import PlaceIfPossibleConfig
import random


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
            configuration (AddBordersConfig): Configuration for adding borders to
        """
        point_collection = configuration.point_collection
        map_layer_type = configuration.map_layer_type
        obj_type: AOE2ObjectType = configuration.obj_type
        player_id = configuration.player_id
        border_width = configuration.border_width

        if player_id is None:
            player_id = DEFAULT_PLAYER

        points = point_collection.get_point_list_copy()

        # As points are added to the original point manager
        # They get removed, however that interferes with the loop
        # that calculates whether or not a point is on the border.
        copy_point_collection = point_collection.copy()

        for point in points:
            if self.__is_on_border(copy_point_collection, point, border_width):

                # margin 0 since each wall is placed next to other wall pieces
                self.place_if_possible(
                    PlaceIfPossibleConfig(
                        point_collection=point_collection,
                        map_layer_type=map_layer_type,
                        obj_type=obj_type,
                        starting_point=point,
                        player_id=player_id,
                        margin=0,
                    )
                )

        return

    def create_block_like_borders(
        self,
        point_collection: PointCollection,
        map_layer_type: MapLayerType,
        obj_type: AOE2ObjectType,
        player_id: PlayerId,
    ) -> None:
        """
        Incomplete ****
        """
        points_list = point_collection.get_point_list()

        points_away_from_border = []

        for point in points_list:
            if self.__is_on_border(point_collection, point, 5):
                continue
            points_away_from_border.append(point)

        random_point = points_away_from_border[
            random.randint(0, len(points_away_from_border) - 1)
        ]

    def __is_on_border(
        self,
        point_collection: PointCollection,
        point: tuple[int, int],
        border_width: int,
    ):
        """
        Checks if given point is on a border.

        Args:
            points: Set of all points in space.
            point: single point to find distance for.
            border_width: Number of squares to fill in along the edge.
        """
        x, y = point

        for i in range(-border_width, border_width + 1):
            for j in range(-abs(abs(i) - border_width), abs(abs(i) - border_width) + 1):
                neighbor_point = (x + i, y + j)
                point_exists = point_collection.check_point_exists(neighbor_point)
                if not point_exists:
                    return True

        return False
