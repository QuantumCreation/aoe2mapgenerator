"""Village template: a living medieval settlement with farms, resources,
villagers, military, and natural decorations.

Clicking to set the centre
--------------------------
Pass ``center_point=(x, y)`` to anchor the village to a specific tile.
If omitted the centroid of *point_collection* is used — selecting a region in
the map editor before generating is sufficient to control placement.
"""

from typing import Tuple

from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.settlement_helpers import place_village_interior
from aoe2mapgenerator.templates.template_decorator import register_template
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


@register_template(TemplateType.VILLAGE)
class VillageTemplate(AbstractTemplate):
    """Generates a living medieval village settlement (no perimeter walls).

    Layout (from the centre outward)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. **Town Center** — at the village centre.
    2. **Mill + Farms** — Mill NW of centre, 6 farms clustered around it.
    3. **Barracks** — SE of centre.
    4. **Watch Towers** — two towers near the village edge (NW and SW).
    5. **Gaia resources** — stone mine (NE), gold mine (S), forage/fruit
       bushes (W), deer herd (E), sheep (S), small pond (SW).
    6. **Tree clusters** — 3 oak/tree splashes at scattered diagonal offsets.
    7. **Paths** — dirt roads from the Town Center to the Mill, Barracks,
       and all four cardinal edges of the village.
    8. **Troops** — Spearmen (inner), Man-at-Arms (mid), Archers (outer/edge).
    9. **Villagers** — 8 specialised villager units placed throughout the area
       (farmer, forager, lumberjack, shepherd, builder, general, …).

    Keyword arguments accepted by ``generate()``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - ``center_point`` (tuple[int, int]): Centre tile.  If omitted, defaults
      to the centroid of *point_collection* (click-to-place).
    - ``radius`` (int): Bounding radius for the entire village.  Default ``20``.
    - ``player_id`` (PlayerId): Owning player.  Default ``PlayerId.ONE``.
    """

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        *args,
        **kwargs,
    ) -> PointCollection:
        radius: int = kwargs.get("radius", 20)
        player_id: PlayerId = kwargs.get("player_id", PlayerId.ONE)

        # Falls back to the centroid when no specific tile is provided.
        center_point: Tuple[int, int] = kwargs.get(
            "center_point",
            point_collection.get_average_point_position(),
        )

        return place_village_interior(
            map_manager=map_manager,
            point_collection=point_collection,
            center_point=center_point,
            radius=float(radius),
            player_id=player_id,
        )
