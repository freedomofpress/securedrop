#!/bin/bash
#

set -e

SVC_ACCT_FILE=/gce-svc-acct.json

# Try to authenticate Google tooling
gcloud auth activate-service-account \
    --key-file "${SVC_ACCT_FILE}" > /dev/null

# Run the container in background, allows subsequent system calls
if [ "$1" = "background" ]; then
    tail -f /dev/null
else
    /usr/bin/gcloud "$@"
fi
