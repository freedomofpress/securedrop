#!/bin/bash
# shellcheck disable=SC2209
#
# Wrapper around debian build logic to bootstrap virtualenv

set -e
set -u
set -o pipefail

. ./devops/scripts/boot-strap-venv.sh

virtualenv_bootstrap

make build-debs
