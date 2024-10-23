#!/bin/bash
# shellcheck disable=SC2209,SC2086
# Build specified packages. This runs *outside* the container.

set -euxo pipefail

git --no-pager log -1 --oneline --show-signature --no-color

OCI_RUN_ARGUMENTS="--user=root -v $(pwd):/src:Z"

# Default to podman if available
if which podman > /dev/null 2>&1; then
    OCI_BIN="podman"
    # Make sure host UID/GID are mapped into container,
    # see podman-run(1) manual.
    OCI_RUN_ARGUMENTS="${OCI_RUN_ARGUMENTS} --userns=keep-id"
else
    OCI_BIN="docker"
fi
# Pass -it if we're a tty
if test -t 0; then
    OCI_RUN_ARGUMENTS="${OCI_RUN_ARGUMENTS} -it"
fi

export OCI_RUN_ARGUMENTS
export OCI_BIN

WHAT="${WHAT:-securedrop}"
export UBUNTU_VERSION="${UBUNTU_VERSION:-focal}"

cd "$(git rev-parse --show-toplevel)"

. ./builder/image_prep.sh

mkdir -p "build/${UBUNTU_VERSION}"

if [[ $WHAT == "ossec" ]]; then
    # We need to build each variant separately because it dirties the container
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        -e VARIANT=agent --entrypoint "/build-debs-ossec" \
        fpf.local/sd-server-builder-${UBUNTU_VERSION}
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        -e VARIANT=server --entrypoint "/build-debs-ossec" \
        fpf.local/sd-server-builder-${UBUNTU_VERSION}
else
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        --entrypoint "/build-debs-securedrop" \
        fpf.local/sd-server-builder-${UBUNTU_VERSION}
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
