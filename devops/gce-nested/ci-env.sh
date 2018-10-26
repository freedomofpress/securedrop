#!/bin/bash
# shellcheck disable=SC2162,SC2034
#
# Mimic CI, set up the all the required environment variables to match the
# nested virtualization tests

ROOTDIR="$(git rev-parse --show-toplevel)"
GCE_CREDS_FILE="${ROOTDIR}/ci-gce.creds"

if [ -z "${CURCLE_BUILD_NUM}"]; then
    export CIRCLE_BUILD_NUM="${USER}"
fi

if [ -z "${GOOGLE_CREDENTIALS}" ]; then
    export GOOGLE_CREDENTIALS="$(cat ${GCE_CREDS_FILE})"
elif [ ! -f "${CURDIR}/ci-gce.creds" ]; then
    echo "${GOOGLE_CREDENTIALS}" > "${GCE_CREDS_FILE}"
fi

export BUILD_NUM="${CIRCLE_BUILD_NUM}"
export PROJECT_ID=securedrop-ci
export JOB_NAME=sd-ci-nested
export GCLOUD_MACHINE_TYPE=n1-standard-2
export GCLOUD_CONTAINER_VER="$(cat ${ROOTDIR}/devops/gce-nested/gcloud-container.ver)"
export CLOUDSDK_COMPUTE_ZONE=us-west1-c
export EPHEMERAL_DIRECTORY="/tmp/gce-nested"
