"""aoe2mapgenerator — procedural AoE2 DE map generation library.

Public API
----------
Import from this top-level package for the stable, versioned surface::

    from aoe2mapgenerator import MapManager, ScenarioConfig, PlayerConfig
    from aoe2mapgenerator import TemplateType, MapLayerType, GateType
    from aoe2mapgenerator import PlaceGroupsConfig, VoronoiGeneratorConfig

Anything not listed in ``__all__`` is considered internal and may change
without notice between minor releases.
"""

# ------------------------------------------------------------------
# Third-party compatibility shims (must run before any serialization)
# ------------------------------------------------------------------
from aoe2mapgenerator.common import compat as _compat  # noqa: F401  (side effect: numpy-safe parser)

# ------------------------------------------------------------------
# Core façade
# ------------------------------------------------------------------
from aoe2mapgenerator.map.map_manager import MapManager

# ------------------------------------------------------------------
# Map data model
# ------------------------------------------------------------------
from aoe2mapgenerator.map.map import Map
from aoe2mapgenerator.map.imap_manager import IMapManager

# ------------------------------------------------------------------
# Enumerations (re-exported from common.enums for convenience)
# ------------------------------------------------------------------
from aoe2mapgenerator.common.enums.enum import GateType, MapLayerType
from aoe2mapgenerator.templates.template_types import TemplateType

# ------------------------------------------------------------------
# Placer configuration dataclasses
# ------------------------------------------------------------------
from aoe2mapgenerator.units.placers.placer_configs import (
    AddBordersConfig,
    PlaceGateOnEightSidesConfig,
    PlaceGateOnFourSidesConfig,
    PlaceGroupsConfig,
    PlacePathConfig,
    PointSelectorConfig,
    VisualizeMapConfig,
    VoronoiGeneratorConfig,
)

# ------------------------------------------------------------------
# Point collections (used as input / output of many methods)
# ------------------------------------------------------------------
from aoe2mapgenerator.units.placers.point_management.point_manager import PointCollection

# ------------------------------------------------------------------
# Terrain generation
# ------------------------------------------------------------------
from aoe2mapgenerator.terrain.terrain import PerlinTerrainConfig, PerlinTerrainGenerator, PerlinNoiseConfig, TerrainBand

# ------------------------------------------------------------------
# Scenario configuration
# ------------------------------------------------------------------
from aoe2mapgenerator.scenario.scenario_config import (
    PlayerConfig,
    ScenarioConfig,
    configure_scenario,
)

# ------------------------------------------------------------------
# Trigger helpers
# ------------------------------------------------------------------
from aoe2mapgenerator.triggers.triggers import TriggerManager
from AoE2ScenarioParser.datasets.trigger_lists.attack_stance import AttackStance
from AoE2ScenarioParser.datasets.trigger_lists.diplomacy_state import DiplomacyState
from AoE2ScenarioParser.datasets.trigger_lists.attribute import Attribute
from AoE2ScenarioParser.datasets.trigger_lists.operation import Operation

# ------------------------------------------------------------------
# AoE2ScenarioParser re-exports used in every map script
# ------------------------------------------------------------------
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.units import UnitInfo
from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.object_support import Civilization, StartingAge

__all__ = [
    # façade
    "MapManager",
    # data model
    "Map",
    "IMapManager",
    # enums
    "GateType",
    "MapLayerType",
    "TemplateType",
    # configs
    "AddBordersConfig",
    "PlaceGateOnEightSidesConfig",
    "PlaceGateOnFourSidesConfig",
    "PlaceGroupsConfig",
    "PlacePathConfig",
    "PointSelectorConfig",
    "VisualizeMapConfig",
    "VoronoiGeneratorConfig",
    # points
    "PointCollection",
    # terrain
    "PerlinTerrainConfig",
    "PerlinTerrainGenerator",
    "PerlinNoiseConfig",
    "TerrainBand",
    # scenario
    "PlayerConfig",
    "ScenarioConfig",
    "configure_scenario",
    # triggers
    "TriggerManager",
    "AttackStance",
    "DiplomacyState",
    "Attribute",
    "Operation",
    # AoE2ScenarioParser datasets
    "PlayerId",
    "UnitInfo",
    "BuildingInfo",
    "TerrainId",
    "Civilization",
    "StartingAge",
]
