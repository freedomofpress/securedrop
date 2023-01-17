set -euxo pipefail

cd "$(git rev-parse --show-toplevel)"

# First see if the image exists or not
missing=false
$DOCKER_BIN inspect fpf.local/sd-server-builder > /dev/null 2>&1 || missing=true

if $missing; then
    # Build it if it doesn't
    $DOCKER_BIN build -t fpf.local/sd-server-builder builder/ --no-cache
fi

# Uncomment the following for fast development on adjusting builder logic
# $DOCKER_BIN build -t fpf.local/sd-server-builder builder/

# Run the dependency check
status=0
$DOCKER_BIN run --rm -it -v $(pwd):/src --entrypoint "/dep-check" fpf.local/sd-server-builder || status=$?

if [[ $status == 42 ]]; then
    # There are some pending updates, so force rebuilding the image from scratch
    # and try again!
    echo "Rebuilding container to update dependencies"
    $DOCKER_BIN rmi fpf.local/sd-server-builder
    $DOCKER_BIN build -t fpf.local/sd-server-builder builder/ --no-cache
fi

if [[ $status != 0 ]]; then
    # If there's some other error, exit now
    exit $status
fi
