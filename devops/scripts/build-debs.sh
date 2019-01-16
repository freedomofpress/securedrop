#!/bin/bash
# shellcheck disable=SC2209
#
# Wrapper around debian build logic to bootstrap virtualenv

set -e
set -u
set -o pipefail

. ./devops/scripts/boot-strap-venv.sh

virtualenv_bootstrap

if [[ "${CIRCLE_BRANCH:-}" != docs-* ]]; then
    case "${1:-test}" in
        notest)
            molecule_action=converge
            ;;
        test)
            molecule_action=test
            ;;
    esac

    if [[ "${1:-trusty}" = "xenial" ]]; then
	molecule converge -s builder -- -e securedrop_build_xenial_support=True;
    else
    	molecule "${molecule_action}" -s builder
    fi

else
    echo Not running on docs branch...
fi
