#!/bin/bash
set -u
set -e


# Directory should already exist, from the CI Molecule scenario,
# but let's be certain.
mkdir -p junit

# Combine tests for export as artifacts. There are at least two XML files,
# one from the application tests, and another from the config tests.
./devops/scripts/combine-junit.py ./*results.xml > ./junit/junit.xml
