#!/bin/bash

# bail out on errors
set -e

# declare function for EXIT trap
function cleanup {
    # If the previous build in snap-ci failed, the droplet
    # will still exist. Ensure that it's gone with a pre-emptive destroy.
    echo "Destroying droplet..."
    vagrant destroy development -f
}

# Ensure that DigitalOcean droplet will be cleaned up
# even if script errors (e.g., if serverspec tests fail).
trap cleanup EXIT

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up development --no-provision --provider digital_ocean
vagrant provision development

if (( ${SNAP_WORKER_TOTAL:-0} < 2 )); then
    echo "Not enough workers to run tests."
    exit -1
fi

case "$SNAP_WORKER_INDEX" in
    1)
        # Run application tests
        vagrant ssh development --command 'export DISPLAY=:1; cd /vagrant/securedrop && ./manage.py test'
        ;;
    2)
        # Run serverspec tests
        cd /var/snap-ci/repo/spec_tests/
        bundle exec rake spec:development
        ;;
esac
