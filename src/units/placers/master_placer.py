from src.units.placers.gate_placer import GatePlacer
from src.units.placers.group_placer import GroupPlacer
from src.units.placers.placer_base import PlacerBase
from src.units.placers.wall_placer import WallPlacer
from src.units.placers.point_management.point_manager import PointCollection
from src.units.placers.placer_configs import (
    PlaceClosestToPointConfig,
    PlaceIfPossibleConfig,
    PlaceMultipleConfig,
    FillConfig,
    AddBordersConfig,
    CreateBlockLikeBordersConfig,
    PlaceGateOnFourSidesConfig,
    PlaceGateOnEightSidesConfig,
    PlaceGroupsConfig,
    AddBordersConfig,
)
from src.map.map import Map
from src.units.placers.path_placer import PathPlacer

class MasterPlacer:
    def __init__(self, aoe2_map: Map):
        self.base_placer = PlacerBase(aoe2_map)
        self.wall_placer = WallPlacer(aoe2_map)
        self.gate_placer = GatePlacer(aoe2_map)
        self.group_placer = GroupPlacer(aoe2_map)
        self.path_placer = PathPlacer(aoe2_map)

    def place_closest_to_point(self, config: PlaceClosestToPointConfig) -> None:
        self.base_placer.place_closest_to_point(config)

    def place_if_possible(self, config: PlaceIfPossibleConfig) -> None:
        self.base_placer.place_if_possible(config)

    def place_multiple(self, config: PlaceMultipleConfig) -> None:
        self.base_placer.place_multiple(config)

    def fill(self, config: FillConfig) -> None:
        self.base_placer.fill(config)

    def add_borders(self, config: AddBordersConfig) -> None:
        self.wall_placer.add_borders(config)

    def create_block_like_borders(self, config: CreateBlockLikeBordersConfig) -> None:
        self.wall_placer.create_block_like_borders(config)

    def place_gate_on_four_sides(self, config: PlaceGateOnFourSidesConfig) -> None:
        self.gate_placer.place_gate_on_four_sides(config)

    def place_gate_on_eight_sides(self, config: PlaceGateOnEightSidesConfig) -> None:
        self.gate_placer.place_gate_on_eight_sides(config)

    def place_groups(self, config: PlaceGroupsConfig) -> None:
        self.group_placer.place_groups(config)

    def create_path(self, config: PlacePathConfig) -> None:
        self.path_placer.create_path(config)
