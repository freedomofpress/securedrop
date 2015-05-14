#!/bin/bash

# bail out on errors
set -e

# declare function for EXIT trap
function cleanup {
    # If the previous build in snap-ci failed, the droplet
    # will still exist. Ensure that it's gone with a pre-emptive destroy.
    echo "Destroying droplet..."
    vagrant destroy /staging/ -f
}

# Ensure that DigitalOcean droplet will be cleaned up
# even if script errors (e.g., if serverspec tests fail).
trap cleanup EXIT

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up /staging/ --no-provision --provider digital_ocean

# Run only the shell provisioner, to ensure the "vagrant"
# user account exists with nopasswd sudo.
vagrant provision /staging/ --provision-with shell
vagrant provision /staging/

# TODO: this ugly reload hell and reprovisioning is to
# accommodate for non-idempotent ansible tasks
vagrant reload /staging/
sleep 180 # wait for servers to come back up
vagrant provision /staging/

# Run serverspec tests
cd /var/snap-ci/repo/spec_tests/
bundle exec rake spec:app-staging
bundle exec rake spec:mon-staging
