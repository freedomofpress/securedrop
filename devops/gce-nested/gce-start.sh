#!/bin/bash
#
#
#

set -u
set -e
set -x

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

# Add oslogin ssh key
gcloud_call compute os-login ssh-keys add \
    --key-file /gce.pub \
    --ttl 2h

if ! gcloud_call compute instances describe "${FULL_JOB_ID}" 2>&1 > /dev/null; then
    # Fire-up remote instance
    gcloud_call compute instances create "${FULL_JOB_ID}" \
        --image="${IMG_LOCATE}" \
        --network securedropci \
        --subnet ci-subnet \
        --metadata enable-oslogin=TRUE
fi
