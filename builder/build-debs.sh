#!/bin/bash
# shellcheck disable=SC2209,SC2086
# Build specified packages. This runs *outside* the container.

set -euxo pipefail

# --- BEGIN keep this section in sync with securedrop-client, so that build logs
# from both repositories can be verified in the same way. ---

git --no-pager log -1 --oneline --show-signature --no-color
# We intentionally want the git tag list to be word-split
# shellcheck disable=SC2046
git --no-pager tag -v $(git tag --points-at HEAD)
# Record if we're building with local (i.e., post-signature) changes present.
git status --short

# --- END keep this section in sync. ---

WHAT="${WHAT:-securedrop}"
# If set, a timestamp is appended to the package version number (see fixup-changelog.sh)
NIGHTLY="${NIGHTLY:-}"

if [[ $WHAT == "admin" ]]; then
    export OS_VERSION="${OS_VERSION:-trixie}"
else
    export OS_VERSION="${OS_VERSION:-noble}"
fi

OCI_RUN_ARGUMENTS="--user=root -v $(pwd):/src:Z -e HOST_UID=$(id -u) -e HOST_GID=$(id -g) -e FAST=${FAST:-} -e NIGHTLY=${NIGHTLY}"

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

echo "::group::Environment"
echo "Running build-debs.sh with the follow environment:"
echo "OS_VERSION='$OS_VERSION'"
echo "WHAT='$WHAT'"
echo "NIGHTLY='$NIGHTLY'"
echo "OCI_BIN='$OCI_BIN'"
echo "OCI_RUN_ARGUMENTS='$OCI_RUN_ARGUMENTS'"
echo "::endgroup::"

cd "$(git rev-parse --show-toplevel)"

echo "::group::Building the builder image"
if [[ $WHAT == "admin" ]]; then
    # Build the admin builder
    . ./builder/image_prep.sh admin
else
    # Build the server builder
    . ./builder/image_prep.sh
fi
echo "::endgroup::"

mkdir -p "build/${OS_VERSION}"

echo "::group::Building debian packages"
if [[ $WHAT == "ossec" ]]; then
    # We need to build each variant separately because it dirties the container
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        -e VARIANT=agent --entrypoint "/build-debs-ossec" \
        fpf.local/sd-server-builder-${OS_VERSION}
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        -e VARIANT=server --entrypoint "/build-debs-ossec" \
        fpf.local/sd-server-builder-${OS_VERSION}
elif [[ $WHAT == "admin" ]]; then
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        --entrypoint "/build-debs-admin" \
        fpf.local/sd-admin-builder-${OS_VERSION}
else
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        --entrypoint "/build-debs-securedrop" \
        fpf.local/sd-server-builder-${OS_VERSION}
fi
echo "::endgroup::"

# Display files in build, for debug purposes
echo "::group::Contents of build directory"
find build
echo "::endgroup::"

NOTEST="${NOTEST:-}"

if [[ $NOTEST == "" ]]; then
    echo "::group::Running tests"
    . ./devops/scripts/boot-strap-venv.sh
    virtualenv_bootstrap

    if [[ $WHAT == "ossec" ]]; then
        pytest -v builder/tests/test_ossec_package.py
    elif [[ $WHAT == "admin" ]]; then
        pytest -v builder/tests/test_admin_package.py
    else
        pytest -v builder/tests/test_securedrop_deb_package.py
    fi
    echo "::endgroup::"
fi
