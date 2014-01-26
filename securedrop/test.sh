#!/bin/bash

# -f makes unittest fail fast, so we can use && to avoid burying test failures
python -m unittest -fv tests.unit_tests && python -m unittest -fv tests.functional_tests
