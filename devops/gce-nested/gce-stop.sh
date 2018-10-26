#!/bin/bash
#
#
#

set -u
set -e

CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
. "${CURDIR}/gce.source"

# Destroy remote instance
gcloud_call --quiet compute instances delete "${JOB_NAME}-${BUILD_NUM}"
