#!/bin/bash
# shellcheck disable=SC2162,SC2034
#
# Mimic CI, set up the all the required environment variables to match the
# nested virtualization tests

export CIRCLE_BUILD_NUM="${USER}"
export BUILD_NUM="${CIRCLE_BUILD_NUM}"
export PROJECT_ID=securedrop-ci
export JOB_NAME=sd-ci-nested
export GCLOUD_CONTAINER_VER="$(cat molecule/gce-nested/gcloud-container.ver)"
export CLOUDSDK_COMPUTE_ZONE=us-west1-c
export MOLECULE_EPHEMERAL_DIRECTORY="/tmp/molecule/${PWD##*/}/gce-nested"
export GOOGLE_CREDENTIALS="$(cat ci-gce.creds)"
