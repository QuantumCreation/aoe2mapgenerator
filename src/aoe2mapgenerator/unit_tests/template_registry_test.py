import pytest
from AoE2ScenarioParser.datasets.players import PlayerId

from aoe2mapgenerator.map.imap_manager import IMapManager
from aoe2mapgenerator.templates.abstract_template import AbstractTemplate
from aoe2mapgenerator.templates.template_types import TemplateType
from aoe2mapgenerator.templates.templates_manager import TemplateManager
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection


class _TemplateA(AbstractTemplate):
    def __init__(self, name: str = "A", description: str = "A") -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.ONE,
        **kwargs,
    ) -> PointCollection:
        return point_collection


class _TemplateB(AbstractTemplate):
    def __init__(self, name: str = "B", description: str = "B") -> None:
        self.name = name
        self.description = description

    @staticmethod
    def generate(
        map_manager: IMapManager,
        point_collection: PointCollection,
        player_id: PlayerId = PlayerId.ONE,
        **kwargs,
    ) -> PointCollection:
        return point_collection


def test_template_manager_rejects_duplicate_template_type_registration() -> None:
    manager = TemplateManager()
    manager.register_template(TemplateType.FORT, _TemplateA)

    with pytest.raises(ValueError, match="Template registration collision"):
        manager.register_template(TemplateType.FORT, _TemplateB)

    assert manager.templates[TemplateType.FORT] is _TemplateA


def test_template_manager_allows_explicit_template_replacement() -> None:
    manager = TemplateManager()
    manager.register_template(TemplateType.FORT, _TemplateA)
    manager.register_template(TemplateType.FORT, _TemplateB, replace=True)

    assert manager.templates[TemplateType.FORT] is _TemplateB
