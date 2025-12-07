"""
Perlin noise generator.
"""

import random

import matplotlib.pyplot as plt
import numpy as np
from noise import pnoise2
from aoe2mapgenerator.map.map_object import MapObject

from aoe2mapgenerator.units.placers.point_management.point_manager import (
    PointCollection,
)
from aoe2mapgenerator.units.placers.placer_base import PlacerBase

import random

from typing import List
import matplotlib.pyplot as plt
from typing import Any, Union


class PerlinGenerator(PlacerBase):
    """
    Class for generating perlin patterns.
    """

    def generate_perlin(
        self,
        point_collection: PointCollection,
        sections: int,
        octaves: List[int],
        noise_size: float,
    ) -> list[list[float]]:
        """
        Generates perlin pattern safely.

        Args:
            sections(int): Number of sections to split into.
            seed(int): Seed for the perlin noise.

        Returns:
            list[MapObject]: List of map objects generated from the perlin pattern.
        """

        top_left_point = point_collection.get_theoretical_top_left_corner_point()
        bottom_right_point = (
            point_collection.get_theoretical_bottom_right_corner_point()
        )

        x_width = bottom_right_point[0] - top_left_point[0]
        y_width = bottom_right_point[1] - top_left_point[1]

        noise_matrix = self.__create_perlin_noise_matrix(
            octaves, x_width, y_width, noise_size, sections
        )

        return noise_matrix

    def display(self, image: List[List[float]], cmap: str = "gray") -> None:
        """Plot the given image."""
        plt.imshow(image, cmap=cmap)
        plt.show()

    def __create_perlin_noise_matrix(
        self,
        octaves: List[int],
        x_width: int,
        y_width: int,
        noise_size: float,
        splits: int,
    ) -> List[List[float]]:
        """
        Main execution function to generate and plot Perlin noise.

        Args:
            octaves (List[int]): List of octaves to generate noise.
            n (int): Size of the final picture.
            size (int): Size of the noise.
            splits (int): Number of sections to split the contrast.
        """
        seed = self.__generate_seed()
        real_seed = seed * 10

        combined_noise_matrix: List[List[float]] = [
            [0 for _ in range(y_width)] for _ in range(x_width)
        ]

        for index, octave in enumerate(octaves):
            self.__generate_perlin_noise(
                combined_noise_matrix, noise_size, real_seed, octave
            )

        self.__contrast_split(combined_noise_matrix, splits)
        return combined_noise_matrix

    def __generate_perlin_noise(
        self, matrix: List[List[float]], noise_size: float, real_seed: int, octave: int
    ) -> List[List[float]]:
        """
        Generate Perlin noise for given parameters.

        Args:
            xpix (int): Number of pixels in x direction.
            ypix (int): Number of pixels in y direction.
            size (int): Size of the noise.
            real_seed (int): Seed for the noise.
            octave (int): Octave of the noise.
        """
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                noise_val = pnoise2(
                    (i / len(matrix)) * noise_size + real_seed,
                    (j / len(matrix[i])) * noise_size + real_seed,
                    octave,
                    0.8,
                )
                matrix[i][j] += noise_val

        return matrix

    def __contrast_split(self, matrix: List[List[float]], sections: int = 2) -> None:
        """
        Split the contrast of the array into sections.

        Args:
            array (List[List[float]]): Array to split contrast.
            sections (int): Number of sections to split the contrast.
        """
        min_val = np.min(matrix)
        max_val = np.max(matrix)

        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                matrix[i][j] = self.__contrast_split_single(
                    matrix[i][j], min_val, max_val, sections
                )

    def __contrast_split_single(
        self, value: float, min_val: float, max_val: float, sections: int = 2
    ) -> float:
        """
        Split the contrast of a single value into sections. For example, if sections = 2, min_val = 0, max_val = 1,
        then 0.25 will be categorized as 0.0 and 0.75 will be categorized as 1.0.

        Args:
            value (float): Value to split contrast.
            min_val (float): Minimum value of the array.
            max_val (float): Maximum value of the array.
            sections (int): Number of sections to split the contrast.

        Returns:
            float: Value after contrast split.
        """
        diff = max_val - min_val
        for i in range(sections):
            if value < (min_val + (((i + 1) * diff) / sections)):
                return i / sections
        return i / sections

    def __add_matrices(
        self, a: List[List[float]], b: List[List[float]]
    ) -> List[List[float]]:
        """
        Add two nested arrays element-wise.

        Args:
            a (List[List[float]]): First array.
            b (List[List[float]]): Second array.

        Returns:
            List[List[float]]: Resultant array after addition.
        """
        final = []
        for row_a, row_b in zip(a, b):
            final.append([x + y for x, y in zip(row_a, row_b)])
        return final

    def __generate_seed(self) -> int:
        """Generate a random seed."""
        return random.randint(0, 100)
