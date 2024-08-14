#!/bin/bash
# Destroys GCE instances used for CI. This script will be run by CI
# regardless of pass/fail state of tests, to ensure instances don't
# remain running, incurring additional costs.

set -u
set -e

TOPLEVEL="$(git rev-parse --show-toplevel)"
# shellcheck source=devops/gce-nested/ci-env.sh
. "${TOPLEVEL}/devops/gce-nested/ci-env.sh"

# Destroy remote instance
gcloud_call compute instances delete "${JOB_NAME}-${BUILD_NUM}"
