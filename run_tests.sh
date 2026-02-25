#!/bin/bash
# run_tests.sh
poetry install && PYTHONPATH=src poetry run pytest src/aoe2mapgenerator/unit_tests/ "$@" --disable-warnings
