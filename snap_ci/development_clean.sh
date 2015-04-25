#!/bin/bash

# bail out on errors
set -e

# If the previous build in snap-ci failed, the droplet 
# will still exist. Ensure that it's gone with a pre-emptive destroy.
vagrant destroy development -f

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up development --no-provision
vagrant provision development

# Run serverspec tests
cd /var/snap-ci/repo/spec_tests/
# TODO: Need to fix versioning mismatch of what is installed on snap-ci compared
# to tests. Commented out running serverspec tests till then.
bundle exec rake spec:development

# Destroy the droplets since you will want to start builds with a fresh tagged
# release and to save money.
vagrant destroy development -f
