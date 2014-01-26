#!/bin/bash

# -f makes unittest fail fast, so we can use && to avoid burying test failures
python -m unittest -f tests.unit_tests && python -m unittest -f tests.functional_tests
