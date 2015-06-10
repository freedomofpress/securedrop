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
vagrant ssh development --command "cd /vagrant/securedrop && ./manage.py test"
