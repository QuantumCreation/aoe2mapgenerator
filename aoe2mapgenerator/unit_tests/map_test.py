"""
TODO: Add module description.
"""
import time

import pytest

from aoe2mapgenerator.map.map import Map


@pytest.mark.order(1)
def test_create_map_10():
    """
    Tests the creation of a map with size 500.
    """
    n = 10
    start_time = time.time()
    Map(n)
    end_time = time.time()
    total_time = end_time - start_time

    print(f"Total time: {total_time:.4f} seconds")

    assert total_time < 0.5, f"Performance test failed: total time {total_time:.4f} seconds"

@pytest.mark.order(2)
def test_create_map_500():
    """
    Tests the creation of a map with size 500.
    """
    n = 500
    start_time = time.time()
    Map(n)
    end_time = time.time()
    total_time = end_time - start_time

    assert total_time < 1.5, f"Performance test failed: total time {total_time:.4f} seconds"

# def test_create_map_500_benchmark(benchmark):
#     """
#     Tests the creation of a map with size 500.
#     """
#     n = 500
#     benchmark(Map, n)
