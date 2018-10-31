#!/bin/bash
# shellcheck disable=SC2162,SC2034,SC2059,SC2086,SC2155
#
# Mimic CI, set up the all the required environment variables to match the
# nested virtualization tests

ROOTDIR="$(git rev-parse --show-toplevel)"
GCE_CREDS_FILE="${ROOTDIR}/.gce.creds"

# First check if there is an existing cred file
if [ ! -f "${GCE_CREDS_FILE}" ]; then

    # Oh there isnt one!? Well do we have a google cred env var?
    if [ -z "${GOOGLE_CREDENTIALS}" ]; then
        echo "ERROR: Make sure you set env var GOOGLE_CREDENTIALS"
    # Oh we do!? Well then lets process it
    else
        # Does the env var have a google string it in.. assume we are a json
        if [[ "${GOOGLE_CREDENTIALS}" =~ google ]]; then
            printf "${GOOGLE_CREDENTIALS}" > "${GCE_CREDS_FILE}"
        # otherwise assume we are a base64 string. Thats needed for CircleCI
        else
            printf "${GOOGLE_CREDENTIALS}" | base64 --decode > "${GCE_CREDS_FILE}"
        fi
    fi
fi

if [ -z "${CIRCLE_BUILD_NUM:-}" ]; then
    export CIRCLE_BUILD_NUM="${USER}"
fi

export BUILD_NUM="${CIRCLE_BUILD_NUM}"
export PROJECT_ID=securedrop-ci
export JOB_NAME=sd-ci-nested
export GCLOUD_MACHINE_TYPE=n1-highcpu-4
export GCLOUD_CONTAINER_VER="$(cat ${ROOTDIR}/devops/gce-nested/gcloud-container.ver)"
export CLOUDSDK_COMPUTE_ZONE=us-west1-c
export EPHEMERAL_DIRECTORY="/tmp/gce-nested"
