#!/bin/bash
# shellcheck disable=SC2209
#
# Wrapper around debian build logic to bootstrap virtualenv

set -e
set -o pipefail

. ./devops/scripts/boot-strap-venv.sh

virtualenv_bootstrap

molecule test -s builder-xenial
