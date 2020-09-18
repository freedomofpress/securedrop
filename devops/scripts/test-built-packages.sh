#!/bin/bash
# shellcheck disable=SC2209
#
# Wrapper around debian build logic to bootstrap virtualenv

set -e
set -o pipefail
TARGET_PLATFORM="${1:-xenial}"
. ./devops/scripts/boot-strap-venv.sh

virtualenv_bootstrap

molecule test -s "builder-${TARGET_PLATFORM}"
