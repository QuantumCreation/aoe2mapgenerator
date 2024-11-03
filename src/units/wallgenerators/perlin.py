"""
Perlin noise generator.
"""

import random

import matplotlib.pyplot as plt
import numpy as np
from noise import pnoise2

from aoe2mapgenerator.src.units.placers.placer_base import PlacerBase


class PerlinGenerator(PlacerBase):
    """
    Class for generating perlin patterns.
    """

    def generate_perlin(self, size: int, sections: int, seed: int) -> None:
        """
        Generates perlin noise.

        Args:
            size: Size of the array.
            sections: Number of sections to split into.
            seed: Seed for the perlin noise.
        """
        self._generate_perlin_instance(
            octaves=[25], array_size=size, seed=seed, perlin_size=1, sections=sections
        )

    def _generate_perlin_instance(
        self,
        octaves: list[int],
        array_size: int,
        seed: int,
        perlin_size: int,
        sections: int,
    ) -> list[list]:

        seed = random.randint(0, 100)
        perlin_size = 1

        real_seed = seed * 10

        noise_array = [[0 for i in range(array_size)] for j in range(array_size)]

        for index, octave in enumerate(octaves):
            xpix, ypix = array_size, array_size

            for i in range(xpix):
                for j in range(ypix):
                    noise_val = pnoise2(
                        (i / xpix) * perlin_size + real_seed,
                        (j / ypix) * perlin_size + real_seed,
                        octave,
                        0.8,
                    )
                    noise_array[i][j] += (1 / (2 ** (index + 1))) * noise_val

        contrast_levels = self.contrast_split(noise_array, sections)

        return noise_array

    def display_perlin(self, final_pic: list[list]) -> None:
        """
        Displays the perlin noise.
        """
        plt.imshow(final_pic, cmap="gray")
        plt.show()

    def contrast_split(self, array: list[list], sections=2) -> list[int]:
        """
        Splits an array into sections based on contrast.

        Args:
            array (list[list]): Array to split
            sections (int): Number of sections to split into
        """
        unique_values = set()

        min_val = np.min(array)
        max_val = np.max(array)

        for i, row in enumerate(array):
            for j, value in enumerate(row):
                array[i][j] = self.categorize_split(value, min_val, max_val, sections)
                unique_values.add(array[i][j])

        return list(unique_values)

    def categorize_split(
        self, value: float, min_val: float, max_val: float, sections=2
    ) -> float:
        """
        Categorizes a value into a section for perlin noise

        Args:
            value: Value to categorize
            min: Minimum value
            max: Maximum value
            sections: Number of sections to categorize into
        """

        for i in range(sections):
            if value < (min_val + (i + 1) * (max_val - min_val) / sections):
                return i / sections

        return i / sections
