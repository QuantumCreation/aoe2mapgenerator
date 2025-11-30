# AOE2_Map_Generator
Generates Random AOE2 Maps





# Testing with MYPY

## Running unit tests

This project uses pytest for unit tests and is managed with Poetry. Tests live under `src/unit_tests/`.

Recommended quick commands (from the repository root):

1) Install dependencies (if you haven't already):

```bash
cd aoe2mapgenerator
poetry install
```

2) Run all tests using the helper script:

```bash
./run_tests.sh
```

3) Or run the full unit test suite with Poetry directly:

```bash
poetry run pytest src/unit_tests -q
```

4) Run a single test file or test function:

```bash
# single file
poetry run pytest src/unit_tests/map_test.py -q

# single test function inside a file
poetry run pytest src/unit_tests/map_test.py::test_create_map_10 -q
```

5) Advanced / debugging options:

- Run with verbose output: `poetry run pytest -v`
- Use `-k <expr>` to filter tests by keyword (e.g. `-k create_map`).
- Add `--maxfail=1` to stop on first failure.

If you run tests without Poetry you can still use `pytest` directly, but make sure the Python environment contains the project dependencies.
