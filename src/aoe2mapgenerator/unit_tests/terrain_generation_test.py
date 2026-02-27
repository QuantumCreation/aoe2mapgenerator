from dataclasses import replace

import pytest
from AoE2ScenarioParser.datasets.terrains import TerrainId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.map_manager import MapManager
from aoe2mapgenerator.scenario.scenario import Scenario
from aoe2mapgenerator.terrain.terrain import (
    PerlinNoiseConfig,
    PerlinTerrainConfig,
    PerlinTerrainGenerator,
    TerrainBand,
)
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection


def test_perlin_noise_matrix_is_deterministic_and_normalized():
    generator = PerlinTerrainGenerator(Map(size=4))
    config = PerlinNoiseConfig(seed=7, scale=8.0, octaves=3, persistence=0.6)

    noise_a = generator.generate_noise_matrix(6, 5, config, origin=(10, 20))
    noise_b = generator.generate_noise_matrix(6, 5, config, origin=(10, 20))
    noise_c = generator.generate_noise_matrix(6, 5, replace(config, seed=8), origin=(10, 20))

    assert noise_a == noise_b
    assert noise_a != noise_c
    assert len(noise_a) == 6
    assert len(noise_a[0]) == 5
    assert all(0.0 <= value <= 1.0 for row in noise_a for value in row)


def test_perlin_config_validation():
    with pytest.raises(ValueError):
        PerlinNoiseConfig(scale=0)

    with pytest.raises(ValueError):
        PerlinTerrainConfig(min_elevation=5, max_elevation=3)


def test_perlin_terrain_generator_applies_terrain_and_elevation_to_subset():
    aoe_map = Map(size=8)
    generator = PerlinTerrainGenerator(aoe_map)

    points = PointCollection()
    selected_points = {(2, 2), (2, 3), (3, 2), (4, 4)}
    points.add_points(selected_points)

    config = PerlinTerrainConfig(
        noise=PerlinNoiseConfig(seed=11, scale=6.0, octaves=2),
        point_collection=points,
        terrain_bands=(
            TerrainBand(0.5, TerrainId.DIRT_1),
            TerrainBand(1.0, TerrainId.DIRT_2),
        ),
        min_elevation=2,
        max_elevation=5,
    )

    result = generator.generate_perlin_terrain(config)

    assert result.origin == (2, 2)
    assert result.width == 3
    assert result.height == 3
    assert set(result.applied_points) == selected_points

    terrain_layer = aoe_map.get_map_layer(MapLayerType.TERRAIN)
    elevation_layer = aoe_map.get_map_layer(MapLayerType.ELEVATION)

    for point in selected_points:
        terrain_obj = terrain_layer.get_object_at_point(point).obj_type
        elevation_obj = elevation_layer.get_object_at_point(point).obj_type
        assert isinstance(terrain_obj, TerrainId)
        assert 2 <= int(elevation_obj) <= 5

    assert elevation_layer.get_object_at_point((0, 0)).obj_type == 0
    assert elevation_layer.get_object_at_point((7, 7)).obj_type == 0

    aoe_map_2 = Map(size=8)
    result_2 = PerlinTerrainGenerator(aoe_map_2).generate_perlin_terrain(config)
    assert result.noise_matrix == result_2.noise_matrix
    assert result.elevation_matrix == result_2.elevation_matrix
    assert result.terrain_matrix == result_2.terrain_matrix


class _DummyMapManagerForScenario:
    def __init__(self, size: int):
        self._tiles = {(x, y): _DummyTile() for x in range(size) for y in range(size)}

    def get_tile(self, x: int, y: int):
        return self._tiles[(x, y)]


class _DummyTile:
    def __init__(self) -> None:
        self.terrain_id = None
        self.elevation = None


class _DummyUnitManager:
    def add_unit(self, *args, **kwargs):  # pragma: no cover - should not be called in this test
        raise AssertionError("Unit placement should not be called in this test")


class _DummyAoe2Scenario:
    def __init__(self, size: int):
        self.map_manager = _DummyMapManagerForScenario(size)
        self.unit_manager = _DummyUnitManager()


def test_scenario_write_map_writes_elevation_layer():
    aoe_map = Map(size=4)
    aoe_map.set_point((1, 2), TerrainId.DIRT_2, MapLayerType.TERRAIN)
    aoe_map.set_point((1, 2), 5, MapLayerType.ELEVATION)

    scenario = Scenario.__new__(Scenario)
    scenario.map = aoe_map
    scenario.scenario = _DummyAoe2Scenario(size=4)

    scenario.write_map()

    tile = scenario.scenario.map_manager.get_tile(1, 2)
    assert tile.terrain_id == TerrainId.DIRT_2.value
    assert tile.elevation == 5


def test_map_manager_generate_perlin_terrain_chains_and_updates_map(monkeypatch):
    class _DummyScenarioWrapper:
        def __init__(self, aoe2_map, *_args, **_kwargs):
            self.map = aoe2_map

    monkeypatch.setattr(
        "aoe2mapgenerator.map.map_manager.Scenario",
        _DummyScenarioWrapper,
    )

    manager = MapManager(10)
    point_collection = PointCollection()
    point_collection.add_points({(1, 1), (1, 2), (2, 1), (2, 2)})

    config = PerlinTerrainConfig(
        point_collection=point_collection,
        noise=PerlinNoiseConfig(seed=3, scale=4.0, octaves=2),
        terrain_bands=(
            TerrainBand(0.45, TerrainId.WATER_SHALLOW),
            TerrainBand(1.0, TerrainId.DIRT_1),
        ),
        min_elevation=1,
        max_elevation=4,
    )

    returned = manager.generate_perlin_terrain(config)

    assert returned is manager
    elevation_layer = manager.get_map_layer(MapLayerType.ELEVATION)
    values = {
        int(elevation_layer.get_object_at_point(point).obj_type)
        for point in point_collection.get_point_list()
    }
    assert values
    assert all(1 <= value <= 4 for value in values)
