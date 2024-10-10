set -euxo pipefail
# Build the container if necessary. This runs *outside* the container.

cd "$(git rev-parse --show-toplevel)"

IMAGE_NAME="fpf.local/sd-server-builder-${UBUNTU_VERSION}"

# First see if the image exists or not
missing=false
$OCI_BIN inspect "${IMAGE_NAME}" > /dev/null 2>&1 || missing=true

if $missing; then
    # Build it if it doesn't
    $OCI_BIN build \
        --build-arg=UBUNTU_VERSION="${UBUNTU_VERSION}" \
        -t "${IMAGE_NAME}" builder/ --no-cache
fi

# Uncomment the following for fast development on adjusting builder logic
$OCI_BIN build --build-arg=UBUNTU_VERSION="${UBUNTU_VERSION}" -t "${IMAGE_NAME}" builder/

# Run the dependency check
status=0
$OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
    --entrypoint "/dep-check" "${IMAGE_NAME}" || status=$?

if [[ $status == 42 ]]; then
    # There are some pending updates, so force rebuilding the image from scratch
    # and try again!
    echo "Rebuilding container to update dependencies"
    $OCI_BIN rmi "${IMAGE_NAME}"
    $OCI_BIN build --build-arg=UBUNTU_VERSION="${UBUNTU_VERSION}" \
        -t "${IMAGE_NAME}" builder/ --no-cache
    # Reset $status and re-run the dependency check
    status=0
    $OCI_BIN run --rm $OCI_RUN_ARGUMENTS \
        --entrypoint "/dep-check" "${IMAGE_NAME}" || status=$?
fi

if [[ $status != 0 ]]; then
    # If there's some other error, exit now
    exit $status
fi
