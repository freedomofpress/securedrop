#!/bin/bash
#
#
#

set -u
set -e
set -x

. ./gce.source

# Find latest CI image
IMG_LOCATE=$(gcloud_call compute images list \
    --filter="family:fpf-securedrop AND name ~ ^ci-nested-virt" \
    --sort-by=~Name --limit=1 --format="value(Name)")

# Fire-up remote instance
gcloud_call compute instances create ${JOB_NAME}-${BUILD_NUM} \
    --network securedropci \
    --subnet ci-subnet \
    --metadata enable-oslogin=TRUE
