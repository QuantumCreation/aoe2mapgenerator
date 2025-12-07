#!/bin/bash
# run_tests.sh
poetry install && find ./src/aoe2mapgenerator/unit_tests -iname *.py | xargs pytest "$@" --disable-warnings

