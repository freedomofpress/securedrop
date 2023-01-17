#!/bin/bash
# shellcheck disable=SC2209

set -euxo pipefail

USE_PODMAN="${USE_PODMAN:-}"

# Allow opting into using podman with USE_PODMAN=1
if  [[ -n "${USE_PODMAN}" ]]; then
    DOCKER_BIN="podman"
else
    DOCKER_BIN="docker"
fi
export DOCKER_BIN

WHAT="${WHAT:-securedrop}"

cd "$(git rev-parse --show-toplevel)"

. ./builder/image_prep.sh

if [[ $WHAT == "ossec" ]]; then
    # We need to build each variant separately because it dirties the container
    $DOCKER_BIN run --rm -it -v "$(pwd)":/src -e VARIANT=agent --entrypoint "/build-debs-ossec" fpf.local/sd-server-builder
    $DOCKER_BIN run --rm -it -v "$(pwd)":/src -e VARIANT=server --entrypoint "/build-debs-ossec" fpf.local/sd-server-builder
else
    $DOCKER_BIN run --rm -it -v "$(pwd)":/src --entrypoint "/build-debs-securedrop" fpf.local/sd-server-builder
fi

NOTEST="${NOTEST:-}"

if [[ $NOTEST == "" ]]; then
    . ./devops/scripts/boot-strap-venv.sh
    virtualenv_bootstrap

    if [[ $WHAT == "ossec" ]]; then
        pytest -v builder/tests/test_ossec_package.py
    else
        pytest -v builder/tests/test_securedrop_deb_package.py
    fi
fi
