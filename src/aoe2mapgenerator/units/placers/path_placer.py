import logging
from typing import List, Tuple
import numpy as np
import random

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.common.types import AOE2ObjectType, Point
from aoe2mapgenerator.units.placers.placer_base import PlacerBase
from aoe2mapgenerator.units.placers.placer_configs import PlaceIfPossibleConfig, PlacePathConfig
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection

logger = logging.getLogger(__name__)


class PathPlacer(PlacerBase):
    """Places a winding path between key points on a map layer."""

    def create_path(self, config: PlacePathConfig) -> None:
        """Trace and place a randomised path connecting ``config.key_points``.

        The path is first traced as straight line segments between each
        consecutive pair of key-points, then iteratively randomised by
        injecting extra waypoints and shifting them by ``random_shift_range``
        pixels.  Each randomisation pass corresponds to an entry in
        ``config.num_divisions`` / ``config.random_shift_range``.

        Args:
            config: Path configuration (key points, layer, object type, player,
                num_divisions, random_shift_range).
        """
        logger.debug("create_path: key_points=%s", config.key_points)
        path = self._connect_points(config.key_points)
        for num_div, shift_range in zip(config.num_divisions, config.random_shift_range):
            path = self._connect_points_with_randomization(config.key_points, num_div, shift_range, path)
            logger.debug(
                "create_path: after randomisation (num_div=%s, shift_range=%s) → %d points",
                num_div, shift_range, len(path),
            )
        self._place_path(config.point_collection, path, config.map_layer_type, config.obj_type, config.player_id)
        logger.debug("create_path: placed %d path tiles", len(path))

    def _connect_points(self, point_list: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        returned_points: List[Tuple[int, int]] = []
        for i, (x, y) in enumerate(point_list[:-1]):
            next_point: List[int] = [point_list[(i + 1) % len(point_list)][0], point_list[(i + 1) % len(point_list)][1]]
            points_to_connect: np.ndarray = np.array([[x, y], next_point], dtype=np.int32)
            new_points = self._connect(points_to_connect)
            returned_points.extend(new_points)
        
        return [tuple(point) for point in np.array(returned_points)]

    def _connect_points_with_randomization(self, key_point_list: List[Tuple[int, int]], num_divisions: int, random_shift_range: int, base_points: List[Tuple[int, int]] | None = None) -> List[Tuple[int, int]]:
        if not base_points:
            base_points = self._connect_points(key_point_list)
        else:
            if not self._check_base_point_valid(base_points, key_point_list):
                raise ValueError("Base points must include all key points.")
        new_point_indicies = self._get_indicies_of_key_points(base_points, key_point_list)
        for i in range(num_divisions + 2):
            index = int(((len(base_points) - 1) / (num_divisions + 1)) * (i))
            new_point_indicies.append(index)
        new_point_indicies.sort()
        new_points = [base_points[i] for i in new_point_indicies]
        for i, point in enumerate(new_points):
            if point not in key_point_list:
                new_points[i] = (point[0] + random.randint(-random_shift_range, random_shift_range), point[1] + random.randint(-random_shift_range, random_shift_range))
        randomized_points = self._connect_points(new_points)
        return list(set(randomized_points)) # Remove duplicates

    def _place_path(self, point_collection: PointCollection, path: List[Tuple[int, int]], map_layer_type: MapLayerType, obj_type: AOE2ObjectType, player_id: PlayerId) -> None:
        for point in path:
            config = PlaceIfPossibleConfig(
                point_collection=point_collection,
                map_layer_type=map_layer_type,
                obj_type=obj_type,
                starting_point=point,
                player_id=player_id
            )
            self.place_if_possible(config)

    def _connect(self, ends: np.ndarray) -> np.ndarray:
        d0, d1 = np.abs(np.diff(ends, axis=0).astype(np.int32))[0]
        if d0 > d1:
            return np.c_[np.linspace(ends[0, 0], ends[1, 0], d0 + 1, dtype=np.int32), np.round(np.linspace(ends[0, 1], ends[1, 1], d0 + 1)).astype(np.int32)]
        return np.c_[np.round(np.linspace(ends[0, 0], ends[1, 0], d1 + 1)).astype(np.int32), np.linspace(ends[0, 1], ends[1, 1], d1 + 1, dtype=np.int32)]

    def _check_base_point_valid(self, base_points: List[Tuple[int, int]], key_points: List[Tuple[int, int]]) -> bool:
        for key_point in key_points:
            if key_point not in base_points:
                return False
        return True

    def _get_indicies_of_key_points(self, base_points: List[Tuple[int, int]], key_points: List[Tuple[int, int]]) -> List[int]:
        key_point_indicies: List[int] = []
        for key_point in key_points:
            key_point_indicies.append(base_points.index(key_point))
        return list(reversed(key_point_indicies))
