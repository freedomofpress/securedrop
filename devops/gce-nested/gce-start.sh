#!/bin/bash
#
#
#

set -u
set -e

# Create ephemeral directory
mkdir -p "${EPHEMERAL_DIRECTORY}" || true

# Ensure SSH key in-place
if [ ! -f "${EPHEMERAL_DIRECTORY}/gce.pub" ]; then
    ssh-keygen -f "${EPHEMERAL_DIRECTORY}/gce" -q -P ""
fi

# Ensure docker container is launched
CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
. "${CURDIR}/gce.source"

# Find latest CI image
IMG_LOCATE=$(gcloud_call compute images list \
    --filter="family:fpf-securedrop AND name ~ ^ci-nested-virt" \
    --sort-by=~Name --limit=1 --format="value(Name)")

if ! gcloud_call compute instances describe "${FULL_JOB_ID}" 2>&1 > /dev/null; then
    # Fire-up remote instance
    gcloud_call compute instances create "${FULL_JOB_ID}" \
        --image="${IMG_LOCATE}" \
        --network securedropci \
        --subnet ci-subnet \
        --metadata "ssh-keys=sdci:$(cat ${EPHEMERAL_DIRECTORY}/gce.pub)"

    # Give box a few more seconds for SSH to become available
    sleep 10
fi
