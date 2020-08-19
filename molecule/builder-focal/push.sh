#!/bin/bash
DATE_STR=$(date +"%Y_%m_%d")
QUAY_REPO=quay.io/freedomofpress/sd-docker-builder-focal

set -e
set -x

docker push "${QUAY_REPO}:${DATE_STR}"

echo "# sha256 digest ${QUAY_REPO}:${DATE_STR}" > image_hash
docker inspect --format='{{index .RepoDigests 0}}' "${QUAY_REPO}:${DATE_STR}" \
    | sed 's/.*://g' >> image_hash
