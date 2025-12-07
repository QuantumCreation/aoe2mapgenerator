from dataclasses import dataclass

from aoe2mapgenerator.map.map_object import MapObject
from aoe2mapgenerator.units.placers.point_management.point_collection import PointCollection


@dataclass
class ObjectPlacement:
    """
    Class for object placement.
    """

    objects_placed: int
    objects: dict[MapObject, PointCollection]
