"""
Enum definitions for template types.
"""

from enum import Enum, auto

class TemplateType(Enum):
    """Enum for all available map templates"""
    CASTLE = auto()
    FORT = auto()
    VILLAGE = auto()
    FOREST = auto()
    MOUNTAIN = auto()
    RIVER = auto()
    ROAD = auto()
    MINE = auto()
    OAK_FOREST = auto()
    SNOW_FOREST = auto()
    WALLS = auto()
    CITY = auto()
    PALACE = auto()

    # ── Nature / biome templates ─────────────────────────────────────────
    POND = auto()                   # Freshwater pond with fish and reeds
    RIVER_SEGMENT = auto()          # Flowing river strip with fish
    PINE_FOREST = auto()            # Coniferous pine forest
    WINTER_LANDSCAPE = auto()       # Snow terrain + frozen pond + arctic fauna
    DESERT = auto()                 # Desert sand with palms, cacti, and desert animals
    DESERT_OASIS = auto()           # Desert biome with a central freshwater oasis
    SAVANNAH = auto()               # Dry grassland with acacia/baobab and savannah fauna
    RAINFOREST = auto()             # Dense jungle with exotic flora and fauna
    MEDITERRANEAN = auto()          # Mediterranean grassland with mixed woodland

    # ── Map-content toolkit templates ────────────────────────────────────
    FAUNA_SCATTER = auto()          # Weighted scatter of wild animals (herds + predators)
    BERRY_BUSH = auto()             # Forage/fruit bush scatter (berry patches)
    BANDIT_CAMP = auto()            # Small hostile camp: tents, campfire, bandits
    SNOWY_MOUNTAIN_RANGE = auto()   # Elongated ridgeline of snow mountains + elevation
    LUSH_FOREST = auto()            # Dense mixed forest with berries, fauna, and clearings
