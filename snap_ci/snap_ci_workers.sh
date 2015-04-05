#!/usr/bin/env bash
# looks at $SNAP_WORKER_INDEX and provision the different environments.

if (( ${SNAP_WORKER_TOTAL:-0} < 2 )); then
  echo "Not enough workers to run tests."
  exit -1
fi

case "$SNAP_WORKER_INDEX" in
  1) ./snap_ci/development_upgrade.sh ;;
  2) ./snap_ci/staging_upgrade.sh;;
esac
