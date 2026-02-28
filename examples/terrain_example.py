"""
terrain_example.py
==================
Demonstrates Perlin-noise terrain generation to produce a realistic landscape
with multiple terrain bands (water → beach → grass → dirt).

Run:
    poetry run python examples/terrain_example.py
"""

from aoe2mapgenerator import (
    MapManager,
    PerlinTerrainConfig,
    PerlinTerrainGenerator,
    PerlinNoiseConfig,
    TerrainBand,
)
from AoE2ScenarioParser.datasets.terrains import TerrainId

OUTPUT_DIR = "/tmp"


def main() -> None:
    SIZE = 120

    mg = MapManager(SIZE, output_dir=OUTPUT_DIR, seed=7)

    # Define terrain bands from lowest noise value (water) to highest (rocky dirt).
    terrain_bands = (
        TerrainBand(max_noise=0.20, terrain_id=TerrainId.WATER_SHALLOW),
        TerrainBand(max_noise=0.28, terrain_id=TerrainId.BEACH),
        TerrainBand(max_noise=0.60, terrain_id=TerrainId.GRASS_1),
        TerrainBand(max_noise=0.78, terrain_id=TerrainId.GRASS_3),
        TerrainBand(max_noise=0.90, terrain_id=TerrainId.DIRT_1),
        TerrainBand(max_noise=1.00, terrain_id=TerrainId.DIRT_2),
    )

    noise_config = PerlinNoiseConfig(
        seed=7,
        octaves=6,
        scale=40.0,
        persistence=0.5,
        lacunarity=2.0,
    )

    terrain_config = PerlinTerrainConfig(
        noise=noise_config,
        terrain_bands=terrain_bands,
        min_elevation=0,
        max_elevation=5,
    )

    generator = PerlinTerrainGenerator(mg.map)
    generator.generate_perlin_terrain(terrain_config)

    mg.write_map_and_save("terrain_example.aoe2scenario")
    print(f"Saved: {OUTPUT_DIR}/terrain_example.aoe2scenario")


if __name__ == "__main__":
    main()
