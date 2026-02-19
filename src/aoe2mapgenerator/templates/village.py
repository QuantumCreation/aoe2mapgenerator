"""Village template: open settlement with a central castle and garrison units (no walls)."""

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.map.map_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.settlement_helpers import place_castle_and_garrison
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


@register_template(TemplateType.VILLAGE)
class VillageTemplate(AbstractTemplate):
    """Generates an open village with a castle at the centroid and garrison units.

    Identical to FortTemplate minus the perimeter walls and gates.

    Keyword arguments accepted by ``generate()``:
    - ``radius`` (int): Bounding radius for unit placement.  Default ``12``.
    - ``player_id`` (PlayerId): Owning player.  Default ``PlayerId.ONE``.
    """

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        radius = kwargs.get("radius", 12)
        player_id = kwargs.get("player_id", PlayerId.ONE)
        center_point = point_collection.get_average_point_position()

        return place_castle_and_garrison(
            map_manager, point_collection, center_point, radius, player_id
        )
