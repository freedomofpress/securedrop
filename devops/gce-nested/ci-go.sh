#!/bin/bash
# Wrapper script to managed GCE-based CI runs, specifically:
#
#   * create GCE host
#   * provision staging VMs within GCE host
#   * clean up GCE host
#
# We're using a wrapper script for this functionality to ensure
# that errors propagate up to the CI runner, so that any non-zero
# exit aborts the run and the CI job is marked as failing.
set -e
set -u
set -o pipefail

export BASE_OS="${BASE_OS:-focal}"

# Temporary workaround for old gcloud-sdk image
sudo mkdir -p /etc/systemd/system/docker.service.d
echo -e "[Service]\nEnvironment=\"DOCKER_ENABLE_DEPRECATED_PULL_SCHEMA_1_IMAGE=true\"" | sudo tee -a /etc/systemd/system/docker.service.d/env.conf
sudo systemctl daemon-reload
sudo systemctl restart docker

./devops/gce-nested/gce-start.sh
./devops/gce-nested/gce-runner.sh
./devops/gce-nested/gce-stop.sh
