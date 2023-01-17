#!/bin/bash
# Check if there are outstanding updates. This runs *inside* the container.

apt-get update
if apt-get upgrade -s | grep Inst; then
    # We will catch status=42 in the outer wrapper and trigger
    # a rebuild of the image to pull in the updates
    exit 42
fi

exit 0
