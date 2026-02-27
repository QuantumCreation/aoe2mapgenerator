"""Deterministic Perlin-based terrain and elevation generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from random import Random
from typing import Iterable

import numpy as np

from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.terrains import TerrainId

from aoe2mapgenerator.common.enums.enum import MapLayerType
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection

Point = tuple[int, int]


@dataclass(frozen=True, slots=True)
class TerrainBand:
    """Maps a normalized noise value range to a terrain type.

    ``max_noise`` is inclusive. Bands are evaluated in ascending order.
    """

    max_noise: float
    terrain_id: TerrainId


@dataclass(frozen=True, slots=True)
class PerlinNoiseConfig:
    """Configures deterministic 2D fractal Perlin noise generation."""

    seed: int = 0
    scale: float = 24.0
    octaves: int = 4
    persistence: float = 0.5
    lacunarity: float = 2.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError("PerlinNoiseConfig.scale must be > 0")
        if self.octaves < 1:
            raise ValueError("PerlinNoiseConfig.octaves must be >= 1")
        if self.persistence <= 0:
            raise ValueError("PerlinNoiseConfig.persistence must be > 0")
        if self.lacunarity <= 0:
            raise ValueError("PerlinNoiseConfig.lacunarity must be > 0")


DEFAULT_TERRAIN_BANDS: tuple[TerrainBand, ...] = (
    TerrainBand(0.28, TerrainId.WATER_SHALLOW),
    TerrainBand(0.36, TerrainId.BEACH),
    TerrainBand(0.68, TerrainId.GRASS_2),
    TerrainBand(0.84, TerrainId.DIRT_1),
    TerrainBand(1.00, TerrainId.DIRT_2),
)


@dataclass(frozen=True, slots=True)
class PerlinTerrainConfig:
    """Configures terrain/elevation generation and map application."""

    noise: PerlinNoiseConfig = PerlinNoiseConfig()
    point_collection: PointCollection | None = None
    terrain_bands: tuple[TerrainBand, ...] = DEFAULT_TERRAIN_BANDS
    terrain_layer_type: MapLayerType = MapLayerType.TERRAIN
    elevation_layer_type: MapLayerType = MapLayerType.ELEVATION
    min_elevation: int = 0
    max_elevation: int = 7
    player_id: PlayerId = PlayerId.GAIA

    def __post_init__(self) -> None:
        if self.min_elevation > self.max_elevation:
            raise ValueError("min_elevation must be <= max_elevation")
        if len(self.terrain_bands) == 0:
            raise ValueError("terrain_bands must contain at least one band")

        previous = -1.0
        for band in self.terrain_bands:
            if not 0.0 <= band.max_noise <= 1.0:
                raise ValueError("TerrainBand.max_noise must be in [0, 1]")
            if band.max_noise < previous:
                raise ValueError("terrain_bands must be sorted by ascending max_noise")
            previous = band.max_noise


@dataclass(frozen=True, slots=True)
class PerlinTerrainResult:
    """Materialized noise + classified matrices for the generated bounding box."""

    origin: Point
    width: int
    height: int
    noise_matrix: list[list[float]]
    elevation_matrix: list[list[int]]
    terrain_matrix: list[list[TerrainId]]
    applied_points: tuple[Point, ...]


class PerlinTerrainGenerator:
    """Generates deterministic noise and applies terrain/elevation to a :class:`Map`."""

    def __init__(self, aoe2_map: Map):
        self.map = aoe2_map

    def generate_noise_matrix(
        self,
        width: int,
        height: int,
        config: PerlinNoiseConfig,
        origin: Point = (0, 0),
    ) -> list[list[float]]:
        """Generate a normalized ``width x height`` Perlin noise matrix in ``[0,1]``.

        Vectorised implementation: builds the full coordinate meshgrid once and
        evaluates all octaves with NumPy broadcasts, replacing the former O(w×h)
        Python loop. Output is identical in structure to the original (a list[list[float]]
        where result[x][y] is the noise value at tile (x, y)), and values are in [0, 1].
        """
        if width < 1 or height < 1:
            raise ValueError("width and height must be >= 1")

        perlin = _Perlin2D(config.seed)
        perm = np.array(perlin._perm, dtype=np.int32)  # shape (512,)
        origin_x, origin_y = origin

        # World coordinates for each axis — shape (width,) and (height,)
        wx = np.arange(width, dtype=np.float64) + origin_x + config.offset_x
        wy = np.arange(height, dtype=np.float64) + origin_y + config.offset_y

        # 2D grid: noise_grid[i, j] corresponds to world coord (wx[i], wy[j])
        wx_grid, wy_grid = np.meshgrid(wx, wy, indexing="ij")  # (width, height)

        amplitude = 1.0
        frequency = 1.0
        total = np.zeros((width, height), dtype=np.float64)
        amplitude_sum = 0.0

        for _ in range(config.octaves):
            sx = (wx_grid / config.scale) * frequency
            sy = (wy_grid / config.scale) * frequency
            total += _noise_vectorized(sx, sy, perm) * amplitude
            amplitude_sum += amplitude
            amplitude *= config.persistence
            frequency *= config.lacunarity

        # Normalise from raw sum to [0, 1]
        normalized: np.ndarray = np.clip(
            (total / amplitude_sum + 1.0) / 2.0, 0.0, 1.0
        )
        return normalized.tolist()

    def generate_perlin_terrain(self, config: PerlinTerrainConfig) -> PerlinTerrainResult:
        """Generate terrain/elevation from Perlin noise and write into the map."""
        target_points = tuple(self._resolve_target_points(config.point_collection))
        if len(target_points) == 0:
            raise ValueError("Cannot generate terrain for an empty point selection")

        min_x = min(point[0] for point in target_points)
        min_y = min(point[1] for point in target_points)
        max_x = max(point[0] for point in target_points)
        max_y = max(point[1] for point in target_points)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        origin = (min_x, min_y)

        noise_matrix = self.generate_noise_matrix(width, height, config.noise, origin=origin)
        elevation_matrix = [
            [self._noise_to_elevation(value, config) for value in row]
            for row in noise_matrix
        ]
        terrain_matrix = [
            [self._noise_to_terrain(value, config.terrain_bands) for value in row]
            for row in noise_matrix
        ]

        for x, y in target_points:
            local_x = x - min_x
            local_y = y - min_y
            self.map.set_point(
                (x, y),
                terrain_matrix[local_x][local_y],
                config.terrain_layer_type,
                config.player_id,
            )
            self.map.set_point(
                (x, y),
                elevation_matrix[local_x][local_y],
                config.elevation_layer_type,
                config.player_id,
            )

        return PerlinTerrainResult(
            origin=origin,
            width=width,
            height=height,
            noise_matrix=noise_matrix,
            elevation_matrix=elevation_matrix,
            terrain_matrix=terrain_matrix,
            applied_points=target_points,
        )

    def _resolve_target_points(
        self, point_collection: PointCollection | None
    ) -> Iterable[Point]:
        if point_collection is None:
            size = self.map.size
            return ((x, y) for x in range(size) for y in range(size))
        return point_collection.get_point_list_copy()

    @staticmethod
    def _noise_to_elevation(value: float, config: PerlinTerrainConfig) -> int:
        span = config.max_elevation - config.min_elevation + 1
        if span <= 1:
            return config.min_elevation

        bucket = int(value * span)
        if bucket >= span:
            bucket = span - 1
        return config.min_elevation + bucket

    @staticmethod
    def _noise_to_terrain(value: float, terrain_bands: tuple[TerrainBand, ...]) -> TerrainId:
        for band in terrain_bands:
            if value <= band.max_noise:
                return band.terrain_id
        return terrain_bands[-1].terrain_id


class _Perlin2D:
    """Seeded 2D Perlin noise implementation (returns values roughly in [-1, 1])."""

    _GRADIENTS: tuple[Point, ...] = (
        (1, 1),
        (-1, 1),
        (1, -1),
        (-1, -1),
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
    )

    def __init__(self, seed: int) -> None:
        permutation = list(range(256))
        Random(seed).shuffle(permutation)
        self._perm = permutation + permutation

    def noise(self, x: float, y: float) -> float:
        x0 = floor(x)
        y0 = floor(y)
        xf = x - x0
        yf = y - y0

        xi = x0 & 255
        yi = y0 & 255

        u = _fade(xf)
        v = _fade(yf)

        aa = self._perm[self._perm[xi] + yi]
        ab = self._perm[self._perm[xi] + yi + 1]
        ba = self._perm[self._perm[xi + 1] + yi]
        bb = self._perm[self._perm[xi + 1] + yi + 1]

        x1 = _lerp(_grad(aa, xf, yf), _grad(ba, xf - 1.0, yf), u)
        x2 = _lerp(_grad(ab, xf, yf - 1.0), _grad(bb, xf - 1.0, yf - 1.0), u)
        return _lerp(x1, x2, v)


# Gradient table for vectorised noise — mirrors _Perlin2D._GRADIENTS.
_NOISE_GRADIENTS: np.ndarray = np.array(
    [(1, 1), (-1, 1), (1, -1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)],
    dtype=np.float64,
)


def _noise_vectorized(
    x: np.ndarray,
    y: np.ndarray,
    perm: np.ndarray,
) -> np.ndarray:
    """Vectorised 2D Perlin noise for an array of (x, y) coordinates.

    Args:
        x: World x-coordinates, arbitrary shape.
        y: World y-coordinates, same shape as ``x``.
        perm: 512-element permutation table from :class:`_Perlin2D`.

    Returns:
        Noise values in roughly ``[-1, 1]``, same shape as ``x``.
    """
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    xf = x - x0
    yf = y - y0

    xi = (x0 & 255).astype(np.int32)
    yi = (y0 & 255).astype(np.int32)

    # Quintic fade (same formula as scalar _fade)
    u = xf * xf * xf * (xf * (xf * 6.0 - 15.0) + 10.0)
    v = yf * yf * yf * (yf * (yf * 6.0 - 15.0) + 10.0)

    # Permutation lookups — safe because perm has 512 entries,
    # perm[xi]+yi max = 255+255 = 510, perm[xi+1] max index = 256.
    aa = perm[perm[xi]     + yi    ]
    ab = perm[perm[xi]     + yi + 1]
    ba = perm[perm[xi + 1] + yi    ]
    bb = perm[perm[xi + 1] + yi + 1]

    # Gradient dot products
    gaa = _NOISE_GRADIENTS[aa & 7]  # shape (*grid, 2)
    gba = _NOISE_GRADIENTS[ba & 7]
    gab = _NOISE_GRADIENTS[ab & 7]
    gbb = _NOISE_GRADIENTS[bb & 7]

    dot_aa = gaa[..., 0] * xf          + gaa[..., 1] * yf
    dot_ba = gba[..., 0] * (xf - 1.0) + gba[..., 1] * yf
    dot_ab = gab[..., 0] * xf          + gab[..., 1] * (yf - 1.0)
    dot_bb = gbb[..., 0] * (xf - 1.0) + gbb[..., 1] * (yf - 1.0)

    # Bilinear interpolation (same as scalar _lerp chain)
    x1 = dot_aa + u * (dot_ba - dot_aa)
    x2 = dot_ab + u * (dot_bb - dot_ab)
    return x1 + v * (x2 - x1)


def _fractal_perlin_value(
    x: float,
    y: float,
    config: PerlinNoiseConfig,
    perlin: _Perlin2D,
) -> float:
    amplitude = 1.0
    frequency = 1.0
    total = 0.0
    amplitude_sum = 0.0

    for _ in range(config.octaves):
        sample_x = (x / config.scale) * frequency
        sample_y = (y / config.scale) * frequency
        total += perlin.noise(sample_x, sample_y) * amplitude
        amplitude_sum += amplitude
        amplitude *= config.persistence
        frequency *= config.lacunarity

    normalized = (total / amplitude_sum + 1.0) / 2.0
    return _clamp(normalized, 0.0, 1.0)


def _fade(t: float) -> float:
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def _grad(hash_value: int, x: float, y: float) -> float:
    gx, gy = _Perlin2D._GRADIENTS[hash_value & 7]
    return gx * x + gy * y


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))
