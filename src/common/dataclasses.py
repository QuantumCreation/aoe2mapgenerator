from dataclasses import dataclass

from src.map.map_object import MapObject
from src.units.placers.point_management.point_collection import PointCollection


@dataclass
class ObjectPlacement:
    """
    Class for object placement.
    """

    objects_placed: int
    objects: dict[MapObject, PointCollection]
