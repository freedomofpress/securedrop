#!/bin/bash
# Configure GCE instance to run the SecureDrop staging environment,
# including configuration tests. Test results will be collected as XML
# for storage as artifacts on the build, so devs can review via web.
set -e
set -u


TOPLEVEL="$(git rev-parse --show-toplevel)"
# shellcheck source=devops/gce-nested/ci-env.sh
. "${TOPLEVEL}/devops/gce-nested/ci-env.sh"

REMOTE_IP="$(gcloud_call compute instances describe \
            "${JOB_NAME}-${BUILD_NUM}" \
            --format="value(networkInterfaces[0].accessConfigs.natIP)")"
SSH_TARGET="${SSH_USER_NAME}@${REMOTE_IP}"
SSH_OPTS=(-i "$SSH_PRIVKEY" -o "StrictHostKeyChecking=no" -o "UserKnownHostsFile=/dev/null")

# Wrapper utility to run commands on remote GCE instance
function ssh_gce {
    # We want all args to be evaluated locally, then passed to the remote
    # host for execution, so we can safely disable shellcheck 2029.
    # shellcheck disable=SC2029
    ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "cd ~/securedrop-source/ && $*"
}

# Retrieve XML from test results, for posting as build artifact in CI.
function fetch_junit_test_results() {
    local remote_src
    local local_dest
    remote_src='junit/*xml'
    local_dest='junit/'
    scp "${SSH_OPTS[@]}" "${SSH_TARGET}:~/securedrop-source/${remote_src}" "$local_dest"
}

# Copy up securedrop repo to remote server
function copy_securedrop_repo() {
  rsync -a -e "ssh ${SSH_OPTS[*]}" \
      --exclude admin/.tox \
      --exclude '*.box' \
      --exclude '*.deb' \
      --exclude '*.pyc' \
      --exclude '*.venv' \
      --exclude .python3 \
      --exclude .mypy_cache \
      --exclude securedrop/.sass-cache \
      --exclude .gce.creds \
      --exclude '*.creds' \
      "${TOPLEVEL}/" "${SSH_TARGET}:~/securedrop-source"
}

# Main logic
copy_securedrop_repo
ssh_gce "make build-debs-notest"

# The test results should be collected regardless of pass/fail,
# so register a trap to ensure the fetch always runs.
trap fetch_junit_test_results EXIT

ssh_gce "make staging"
