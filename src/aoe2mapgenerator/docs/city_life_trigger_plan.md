# City Life Trigger Plan

## Goal
Make generated cities feel alive through coordinated movement:
- military patrols on streets and walls
- villager work routes (farm, mine, forage)
- command-center expeditions to map edges
- district-level circulation linked to roads and gates

## Architecture
1. **Low-level trigger helpers (`triggers/triggers.py`)**
   - Add composable methods for patrol and tasking.
   - Keep direct access to AoE2 trigger effects.

2. **High-level city-life orchestrator (`triggers/city_life.py`)**
   - Accept district areas, gate points, city center, palace center, and resource targets.
   - Emit layered trigger sets:
     - district street patrols
     - gate rotation patrols
     - command routes
     - expedition routes
     - villager task + route triggers

3. **Template integration (`templates/city.py`)**
   - Build villager target points from actual generated farms/resources.
   - Invoke orchestrator when `enable_city_life=True`.

## Trigger Layers
1. **District Patrols**
   - Each district area patrols toward nearest gate.

2. **Gate Rotation Patrols**
   - Gate area units patrol to adjacent gate for perimeter circulation.

3. **Command Routes**
   - Palace/command-center guard area patrols to all gate points.

4. **Expedition Patrols**
   - Military and command groups patrol from city core to map edges and back.

5. **Villager Work**
   - Split village area into sub-areas.
   - Assign each sub-area to a work target (farm/stone/gold/forage).
   - Add both tasking and route movement triggers.

## Palace Template Plan
1. Add standalone `PALACE` template type and helper API.
2. Generate:
   - fortified walls + gates
   - corner towers
   - moat rings
   - central keep
   - formal gardens/decor
   - elite garrison units
3. Support optional embedding into city generation (`include_palace`).
