#!/bin/bash
# Configure GCE instance to run the SecureDrop staging environment,
# including configuration tests. Test results will be collected as XML
# for storage as artifacts on the build, so devs can review via web.
set -e
set -u

OS_VERSION="noble"

TOPLEVEL="$(git rev-parse --show-toplevel)"
# shellcheck source=devops/gce-nested/ci-env.sh
. "${TOPLEVEL}/devops/gce-nested/ci-env.sh"

REMOTE_IP="$(gcloud_call compute instances describe \
            "${FULL_JOB_ID}" \
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
      --exclude .gce.creds \
      --exclude '*.creds' \
      "${TOPLEVEL}/" "${SSH_TARGET}:~/securedrop-source"
}

# Main logic
copy_securedrop_repo

# The test results should be collected regardless of pass/fail,
# so register a trap to ensure the fetch always runs.
trap fetch_junit_test_results EXIT

# build server debs
# securedrop-builder (checked out into the workspace by CI) provides the app-code wheels
ssh_gce "OS_VERSION=\"${OS_VERSION}\" BUILDER=securedrop-builder make build-debs-notest"
ssh_gce "OS_VERSION=\"${OS_VERSION}\" make build-debs-ossec-notest"

# build and install securedrop-admin tools and add staging config
ssh_gce "OS_VERSION=\"trixie\" make build-debs-admin-notest"
ssh_gce "mkdir -p /home/sdci/.config/securedrop-admin"
ssh_gce "sudo apt-get update && sudo apt-get install -y ./build/trixie/securedrop-admin_*+trixie_amd64.deb"
ssh_gce "cp ~/securedrop-source/install_files/ansible-base/roles/ossec/files/test_admin_key.pub /home/sdci/.config/securedrop-admin/"
ssh_gce "cp ~/securedrop-source/install_files/ansible-base/roles/app/files/test_journalist_key.pub /home/sdci/.config/securedrop-admin/"

# start staging environment
ssh_gce "OS_VERSION=\"${OS_VERSION}\" make staging"
