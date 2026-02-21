#!/bin/bash
# run_tests.sh
poetry install && poetry run pytest src/aoe2mapgenerator/unit_tests/ "$@" --disable-warnings

