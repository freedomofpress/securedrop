#!/bin/bash

# bail out on errors
set -e

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

# Run serverspec tests
cd /var/snap-ci/repo/spec_tests/
bundle exec rake spec:development

# Destroy the droplets since you will want to start builds with a fresh tagged
# release and to save money.
vagrant destroy development -f
