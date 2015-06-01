#!/bin/bash

# bail out on errors
set -e

# declare function for EXIT trap
function cleanup {
    echo "Destroying droplet..."
    vagrant destroy development -f
}

# Ensure that DigitalOcean droplet will be cleaned up
# even if script errors (e.g., if serverspec tests fail).
trap cleanup EXIT

# If the previous build in snap-ci failed, the droplet
# will still exist. Ensure that it's gone with a pre-emptive destroy.
cleanup

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up development --no-provision --provider digital_ocean
vagrant provision development

# Run serverspec tests
cd /var/snap-ci/repo/spec_tests/
bundle exec rake spec:development

# Run application tests
# Important: these app tests are AFTER spectests because they've been hanging in snap.

# Using 0<&- to close STDIN based on advice here:
# https://docs.snap-ci.com/troubleshooting/#my-build-is-timing-out
# These app tests run fine, but always hang before returning to the shell,
# so the snap-ci stage times out (fails).
vagrant ssh development --command "cd /vagrant/securedrop && ./manage.py test" 0<&-
