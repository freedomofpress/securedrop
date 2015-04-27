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

# If the previous build in snap-ci failed, the droplet 
# will still exist. Ensure that it's gone with a pre-emptive destroy.
vagrant destroy /staging/ -f

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up /staging/ --no-provision
vagrant provision /staging/

# Run serverspec tests
cd /var/snap-ci/repo/spec_tests/
bundle exec rake spec:app-staging
bundle exec rake spec:mon-staging

# Destroy the droplets since you will want to start builds with a fresh tagged
# release and to save money.
vagrant destroy /staging/ -f
