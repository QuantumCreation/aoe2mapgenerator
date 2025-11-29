import numpy as np

class CityWallGenerator:


    def __init__(self, center_point: tuple[int, int], size: int = 100):
        """
        Initializes the CityWallGenerator with a center point.

        Args:
            center_point: The center point of the city wall.
        """
        self._center_point = center_point
        self._map_array = [[0 for _ in range(size)] for _ in range(size)]  # Create a size x size grid
        self._wall_points = []
        self._inside_points = set()

    def generate_city_wall(self) -> None:
        """
        Generates a city wall around the center point.

        Returns:
            None
        """


        self.draw_square(
            self._center_point[0] - 5,
            self._center_point[1] - 5,
            self._center_point[0] + 5,
            self._center_point[1] + 5,
        )
    
    def _random_find_valid_square_addition(self,size: int) -> tuple[int, int, int, int]:
        """
        Finds a valid square addition to the city wall.

        Args:
            size: The size of the square.

        Returns:
            A tuple containing the coordinates of the square.
        """
        length = len(self._wall_points)

        # Pick a random index
        start_point_idx = np.random.randint(0, length)
        start_point = self._wall_points[start_point_idx]
        end_point = self._wall_points[(start_point_idx + 1) % length]
        
        # Find the middle point between start_point and end_point
        middle_x = (start_point[0] + end_point[0]) // 2
        middle_y = (start_point[1] + end_point[1]) // 2
        middle_point = (middle_x, middle_y)

        delta_y = end_point[1] - start_point[1]
        delta_x = end_point[0] - start_point[0]

        # normalize to 1s
        if delta_x < 0:
            delta_x = -1
        elif delta_x > 0:
            delta_x = 1
        if delta_y < 0:
            delta_y = -1
        elif delta_y > 0:
            delta_y = 1

        vector_perpendicular_1 = (-delta_y, delta_x)
        vector_perpendicular_2 = (delta_y, -delta_x)

        # Get the two points to the sides
        side_1 = (middle_point[0] + vector_perpendicular_1[0], middle_point[1] + vector_perpendicular_1[1])
        side_2 = (middle_point[0] + vector_perpendicular_2[0], middle_point[1] + vector_perpendicular_2[1])







    def add_square(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Adds a square to the city wall.

        Args:
            x1: The x-coordinate of the top-left corner.
            y1: The y-coordinate of the top-left corner.
            x2: The x-coordinate of the bottom-right corner.
            y2: The y-coordinate of the bottom-right corner.

        Returns:
            None
        """
        self._wall_points.append((x1, y1))
        self._wall_points.append((x2, y1))
        self._wall_points.append((x2, y2))
        self._wall_points.append((x1, y2))

        inside_points = self.get_points_inside_square(x1, y1, x2, y2)
        self._inside_points.update(inside_points)

    def get_points_inside_square(self, x1: int, y1: int, x2: int, y2: int) -> set[tuple[int, int]]:
        """
        Returns a set of points inside the square defined by (x1, y1) and (x2, y2),
        excluding the border points.

        Args:
            x1: The x-coordinate of the top-left corner.
            y1: The y-coordinate of the top-left corner.
            x2: The x-coordinate of the bottom-right corner.
            y2: The y-coordinate of the bottom-right corner.

        Returns:
            A set of points inside the square but not on the border.
        """
        points = set()
        for x in range(x1 + 1, x2):
            for y in range(y1 + 1, y2):
                points.add((x, y))
        return points
    
    def draw_square(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Draws a square on the map array.

        Args:
            x1: The x-coordinate of the top-left corner.
            y1: The y-coordinate of the top-left corner.
            x2: The x-coordinate of the bottom-right corner.
            y2: The y-coordinate of the bottom-right corner.

        Returns:
            None
        """
        # Define the four corners of the square
        corners = [
            (x1, y1),  # Top-left
            (x2, y1),  # Top-right
            (x2, y2),  # Bottom-right
            (x1, y2),  # Bottom-left
        ]
        
        # Draw lines between the corners to create the square
        for i in range(len(corners)):
            start = corners[i]
            end = corners[(i + 1) % len(corners)]
            self._draw_line(start, end)


    def _draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """
        Draws a line between two points using Bresenham's line algorithm.

        Args:
            start: The starting point of the line.
            end: The ending point of the line.

        Returns:
            A list of points that make up the line.
        """
        points = []
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        dx = abs(dx)
        dy = abs(dy)

        if dx > dy:
            err = dx / 2.0
            while start[0] != end[0]:
                points.append(start)
                err -= dy
                if err < 0:
                    start = (start[0], start[1] + sy)
                    err += dx
                start = (start[0] + sx, start[1])
        else:
            err = dy / 2.0
            while start[1] != end[1]:
                points.append(start)
                err -= dx
                if err < 0:
                    start = (start[0] + sx, start[1])
                    err += dy
                start = (start[0], start[1] + sy)

        for point in points:
            self._map_array[point[1]][point[0]] = 1
        return points
        
    def visualize(self) -> None:
        """
        Visualizes the city wall on the map array using matplotlib.

        Returns:
            None
        """
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(8, 8))
        plt.imshow(self._map_array, cmap='binary', interpolation='nearest')
        plt.title('City Wall Visualization')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.colorbar(label='Wall')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.tight_layout()
        plt.show()

def get_random_line_from_list(lines: list[tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Returns a random line from the given list of lines.

    Args:
        lines: A list of lines.

    Returns:
        A random line from the list.
    """
    random_start = np.random.randint(0, len(lines))
  
    return (lines[random_start], lines[(random_start + 1) % len(lines)])