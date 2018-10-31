#!/bin/bash
# shellcheck disable=SC2162,SC2034,SC2059,SC2086,SC1090,SC2145,SC2035
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
SSH_OPTS="-i ${SSH_PRIV} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

function ssh_gce {
    eval "ssh ${SSH_OPTS} ${SSH_TARGET} \"cd ~/securedrop-source/ && $@\""
}

function scp_gce {
    eval "scp ${SSH_OPTS} ${SSH_TARGET}:~/securedrop-source/$1 $2"
}

# Copy up securedrop repo to remote server
rsync -a -e "ssh ${SSH_OPTS}" \
    --exclude .git \
    --exclude admin/.tox \
    --exclude *.box \
    --exclude *.deb \
    --exclude *.pyc \
    --exclude *.venv \
    --exclude .python3 \
    --exclude .mypy_cache \
    --exclude securedrop/.sass-cache \
    --exclude .gce.creds \
    --exclude *.creds \
    "${TOPLEVEL}/" "${SSH_TARGET}:~/securedrop-source"

# Run staging process
ssh_gce "make build-debs-notest"

# Run staging process
# This needs to always pass so test collection can be performed
ssh_gce "make staging" || export EXIT_CODE="$?"

# Pull test results back for analysis
scp_gce 'junit/*xml' 'junit/'

# not proficient with bash traps..
# someone is welcome to hack this back in with traps
if [ "${EXIT_CODE:-0}" -ne 0 ]; then
    exit 1
fi
