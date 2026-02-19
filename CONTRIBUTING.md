# Contributing to aoe2mapgenerator

Thanks for contributing. This guide covers setup, validation, and the expected workflow.

## Repository Purpose

`aoe2mapgenerator` is a Python library for procedurally generating Age of Empires II maps and exporting `.aoe2scenario` files.

Key package root: `src/aoe2mapgenerator/`.

## Prerequisites

- Python 3.10+
- Poetry (recommended)
- Local AoE2 scenario parser support (`AoE2ScenarioParser` dependency)

## Local Setup

### Poetry (recommended)

```bash
cd /home/joey/Documents/Projects/aoe2mapgenerator
poetry install
```

### pip editable install

```bash
cd /home/joey/Documents/Projects/aoe2mapgenerator
pip install -e .
```

## Running Validation

### Unit tests

```bash
./run_tests.sh
```

Or directly:

```bash
poetry run pytest src/aoe2mapgenerator/unit_tests -q
```

### Type checking

```bash
poetry run mypy src
```

### Run targeted tests

```bash
poetry run pytest src/aoe2mapgenerator/unit_tests/map_test.py -q
poetry run pytest src/aoe2mapgenerator/unit_tests/map_test.py::test_create_map_10 -q
```

## Project Areas

- `map/`: core map container, layer management, map manager facade
- `units/placers/`: placement algorithms and configs
- `units/wallgenerators/`: Voronoi and wall generation logic
- `templates/`: higher-level generation recipes
- `scenario/`: `.aoe2scenario` writing
- `serializer/`: map serialization helpers
- `unit_tests/`: regression and behavior coverage

## Coding Expectations

- Keep `MapManager` as the primary orchestration surface.
- Prefer typed config objects (for example `PlaceGroupsConfig`) over long positional argument lists.
- Preserve map-layer consistency when introducing new mutating behavior.
- Keep serialization and map mutation concerns separate.

## Test Expectations

- Add/modify tests for behavior changes.
- If a visual/regression output changes, document why in the PR.
- Keep new tests deterministic where possible.

## Pull Request Checklist

1. Implement the change with focused scope.
2. Add/update tests in `src/aoe2mapgenerator/unit_tests/`.
3. Run tests and type checks.
4. Update docs (`README.md`, architecture docs) if public behavior changed.
5. Include in PR description:
   - what changed
   - why
   - commands run and results

## Integration Note (GeneralWebsite)

`GeneralWebsite/backend` consumes this library through a local path dependency:

- `GeneralWebsite/backend/pyproject.toml`
- `aoe2mapgenerator = { path = "../../aoe2mapgenerator", develop = true }`

If you change serialization contracts or `MapManager` behavior, update corresponding backend services and API schema handling in `GeneralWebsite/backend/aoe2_generator/services/`.
