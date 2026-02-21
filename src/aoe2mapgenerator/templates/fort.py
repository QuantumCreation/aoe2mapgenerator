"""Fort template: fully-garrisoned fort with a choice of six perimeter shapes.

All wall generators restrict wall segments to the 8 AoE2-valid grid angles
(multiples of 45 °: horizontal, vertical, and both diagonals).

Available shapes (``shape`` kwarg)
------------------------------------
``"square"``
    Axis-aligned square.  Keyword: ``half_size`` (default 16).

``"rectangle"``
    Axis-aligned rectangle.  Keywords: ``width`` (30), ``height`` (20).

``"octagon"``
    Regular screen-octagon with chamfered 45 ° corners.
    Keyword: ``radius`` (16).  Enables 8-side gate placement.

``"star"`` *(default)*
    Vauban bastioned star fort.  Keywords: ``gate_half_span`` (4),
    ``curtain_reach`` (14).

``"voronoi"``
    Organic shape derived from the central cell of a Voronoi diagram, edges
    snapped to 45 ° angles.  Keywords: ``radius`` (18), ``num_sites`` (14),
    ``seed`` (None).

``"grammar"``
    Rectangle mutated by iterative BUMP / NOTCH / CHAMFER grammar rules.
    Keywords: ``base_width`` (26), ``base_height`` (22), ``iterations`` (6),
    ``seed`` (None).

Clicking to set the centre
--------------------------
Pass ``center_point=(x, y)`` to pin the fort to a specific tile.  If omitted
the template uses the centroid of *point_collection*.
"""

from typing import List, Tuple

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.settlement_helpers import (
    place_fort_decorations,
    place_fort_interior,
)
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.gate_utility import AdvancedWallPlacer
from aoe2mapgenerator.units.placers.placer_configs import PlaceClosestToPointConfig
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection
from aoe2mapgenerator.units.wallgenerators.fort_shapes import FortShape, build_fort_shape


@register_template(TemplateType.FORT)
class FortTemplate(AbstractTemplate):
    """Generates a fully-garrisoned fort with a configurable perimeter shape.

    See the module docstring for the six available shapes and their specific
    keyword arguments.

    Common keyword arguments
    ~~~~~~~~~~~~~~~~~~~~~~~~
    - ``shape`` (str): Perimeter shape.  One of ``"square"``, ``"rectangle"``,
      ``"octagon"``, ``"star"`` *(default)*, ``"voronoi"``, ``"grammar"``.
    - ``center_point`` (tuple[int, int]): Centre tile.  Defaults to the
      centroid of *point_collection* (click-to-place).
    - ``gate_type`` (GateType): Wall gate style.  Default ``GateType.CITY_GATE``.
    - ``player_id`` (PlayerId): Owning player.  Default ``PlayerId.ONE``.

    Layout (outermost → innermost)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Fort perimeter walls (shape-dependent).
    2. Guard towers at every corner vertex.
    3. Gates (4-side or 8-side depending on shape).
    4. Exterior gaia decorations.
    5. Castle, road paths, gate guards, military buildings, troop rings.
    """

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        # Center falls back to the centroid of the selection, enabling
        # "click to place" behaviour in the map editor.
        center_point: Tuple[int, int] = kwargs.pop(
            "center_point",
            point_collection.get_average_point_position(),
        )
        shape: str      = kwargs.pop("shape", "star")
        gate_type: GateType = kwargs.pop("gate_type", GateType.CITY_GATE)
        player_id: PlayerId = kwargs.pop("player_id", PlayerId.ONE)

        # ------------------------------------------------------------------
        # Build fort geometry via the shape dispatcher
        # ------------------------------------------------------------------
        # Strip top-level keys that were already extracted above so they are
        # not passed twice to build_fort_shape (which uses 'shape' as a
        # positional argument — a duplicate would raise TypeError).
        _EXTRACTED_KEYS = {"shape", "center_point", "player_id", "gate_type", "size"}
        shape_kwargs = {k: v for k, v in kwargs.items() if k not in _EXTRACTED_KEYS}
        fort_shape: FortShape = build_fort_shape(shape, center_point, **shape_kwargs)

        wall_pts: List[Tuple[int, int]]      = fort_shape.wall_points
        corners: List[Tuple[int, int]]       = fort_shape.corner_points
        gate_positions: List[Tuple[int, int]] = fort_shape.gate_points
        inscribed_radius: float              = fort_shape.inscribed_radius

        # ------------------------------------------------------------------
        # 1. Perimeter walls
        # ------------------------------------------------------------------
        wall_placer = AdvancedWallPlacer(map_manager.get_map())
        wall_type = gate_type.get_building_info_wall()

        wall_point_collection = map_manager.point_manager.add_point_collection(
            "fort_wall_points", wall_pts, True
        )
        intersection = point_collection.intersect(wall_point_collection)
        intersection_editable = intersection.copy()

        wall_placer.place_wall_points(
            map_manager, point_collection, wall_pts, wall_type, player_id
        )

        # Gates — 8-side for octagon / voronoi (irregular), else 4-side
        if fort_shape.use_eight_side_gates:
            map_manager.gate_placer.place_gate_on_eight_sides(
                point_collection=intersection_editable,
                map_layer_type=MapLayerType.UNIT,
                gate_type=gate_type,
                player_id=player_id,
            )
        else:
            map_manager.gate_placer.place_gate_on_four_sides(
                point_collection=intersection_editable,
                map_layer_type=MapLayerType.UNIT,
                gate_type=gate_type,
                player_id=player_id,
            )

        # ------------------------------------------------------------------
        # 2. Flanking guard towers at every corner vertex
        # ------------------------------------------------------------------
        for corner in corners:
            map_manager.base_placer.place_closest_to_point(
                PlaceClosestToPointConfig(
                    point_collection=point_collection,
                    map_layer_type=MapLayerType.UNIT,
                    obj_type=BuildingInfo.GUARD_TOWER,
                    starting_point=corner,
                    player_id=player_id,
                    margin=0,
                )
            )

        # ------------------------------------------------------------------
        # 3. Gaia decorations outside the walls
        # ------------------------------------------------------------------
        place_fort_decorations(
            map_manager=map_manager,
            point_collection=point_collection,
            center_point=center_point,
            radius=inscribed_radius,
            gate_positions=gate_positions,
        )

        # ------------------------------------------------------------------
        # 4. Castle, paths, gate guards, buildings, troop rings
        # ------------------------------------------------------------------
        return place_fort_interior(
            map_manager=map_manager,
            point_collection=point_collection,
            center_point=center_point,
            radius=inscribed_radius,
            gate_positions=gate_positions,
            player_id=player_id,
        )
