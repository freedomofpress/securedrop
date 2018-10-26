#!/bin/bash
#

set -u
set -e

TOPLEVEL="$(git rev-parse --show-toplevel)"
CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
. "${CURDIR}/gce.source"

SSH_USER_NAME=sdci
SSH_PRIV="${EPHEMERAL_DIRECTORY}/gce"
REMOTE_IP=$(gcloud_call compute instances describe \
            "${JOB_NAME}-${BUILD_NUM}" \
            --format="value(networkInterfaces[0].accessConfigs.natIP)")
SSH_TARGET="${SSH_USER_NAME}@${REMOTE_IP}"
SSH_CMD="ssh -i ${SSH_PRIV} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

function ssh_gce {
    eval "${SSH_CMD} ${SSH_TARGET} \"cd ~/securedrop-source/ && $@\""
}

# Copy up securedrop repo to remote server
rsync -a -e "${SSH_CMD}" \
    --exclude .git \
    --exclude admin/.tox \
    --exclude *.box \
    --exclude *.deb \
    --exclude *.pyc \
    --exclude .python3 \
    --exclude .mypy_cache \
    --exclude securedrop/.sass-cache \
    --exclude .gce.creds \
    --exclude *.creds \
    "${TOPLEVEL}/" "${SSH_TARGET}:~/securedrop-source"

# Run staging process
ssh_gce "make build-debs-notest"

# Run staging process
ssh_gce "make staging"
