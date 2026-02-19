"""Fort template: polygonal walls, gates, castle, and garrison units."""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.common.enums.enum import GateType
from aoe2mapgenerator.map.map_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.settlement_helpers import place_castle_and_garrison
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.gate_utility import AdvancedWallPlacer
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


@register_template(TemplateType.FORT)
class FortTemplate(AbstractTemplate):
    """Generates a walled fort with gates, a central castle, and garrison units.

    Keyword arguments accepted by ``generate()``:
    - ``center_point`` (tuple[int, int]): Centre tile.  Default ``(100, 100)``.
    - ``sides`` (int): Number of polygon sides for the wall.  Default ``8``.
    - ``radius`` (int): Half-width of the fort in tiles.  Default ``12``.
    - ``gate_type`` (GateType): Wall gate style.  Default ``GateType.CITY_GATE``.
    - ``player_id`` (PlayerId): Owning player.  Default ``PlayerId.ONE``.
    """

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        center_point = kwargs.get("center_point", (100, 100))
        sides = kwargs.get("sides", 8)
        radius = kwargs.get("radius", 12)
        gate_type = kwargs.get("gate_type", GateType.CITY_GATE)
        player_id = kwargs.get("player_id", PlayerId.ONE)

        # Polygonal walls with gates
        wall_placer = AdvancedWallPlacer(map_manager.get_map())
        wall_placer.generate_polygon_walls_with_gates(
            map_manager=map_manager,
            point_collection=point_collection,
            point=center_point,
            sides=sides,
            radius=radius,
            gate_type=gate_type,
            player_id=player_id,
        )

        return place_castle_and_garrison(
            map_manager, point_collection, center_point, radius, player_id
        )
