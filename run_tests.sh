#!/bin/bash
# run_tests.sh
find ./src/unit_tests -iname *.py | xargs pytest "$@" --disable-warnings

