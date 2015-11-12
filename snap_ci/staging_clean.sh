#!/bin/bash

# bail out on errors
set -e
set -x

# declare function for EXIT trap
function cleanup {
    echo "Destroying droplet..."
    vagrant destroy /staging/ -f
}

# Ensure that DigitalOcean droplet will be cleaned up
# even if script errors (e.g., if serverspec tests fail).
trap cleanup EXIT

# If the previous build in snap-ci failed, the droplet
# will still exist. Ensure that it's gone with a pre-emptive destroy.
cleanup

# Find the root of the git repository. A simpler implementation
# would be `git rev-parse --show-toplevel`, but that must be run
# from inside the git repository, whereas the solution below is
# directory agnostic. Exporting this variable doesn't work in snapci,
# so it must be rerun in each stage.
repo_root=$( dirname "$( cd "$( dirname "${BASH_SOURCE[0]}"  )" && pwd )" )

# Skip "install_local_pkgs" because it requires a special VM,
# and skip "grsec" because DigitalOcean hosts don't support custom kernels.
export ANSIBLE_ARGS="--skip-tags=install_local_packages,grsec"

# Create target hosts, but don't provision them yet. The shell provisioner
# is only necessary for DigitalOcean hosts, and must run as a separate task
# from the Ansible provisioner, otherwise it will only run on one of the two
# hosts, due to the `ansible.limit = 'all'` setting in the Vagrantfile.
vagrant up /staging/ --no-provision --provider digital_ocean

# First run only the shell provisioner, to ensure the "vagrant"
# user account exists with nopasswd sudo, then run Ansible.
vagrant provision /staging/ --provision-with shell
vagrant provision /staging/ --provision-with ansible

# TODO: this ugly reload hell and reprovisioning is to
# accommodate for non-idempotent ansible tasks
vagrant reload /staging/
sleep 180 # wait for servers to come back up
vagrant provision /staging/ --provision-with ansible

# Run serverspec tests
cd "${repo_root}/spec_tests/"
bundle exec rake spec:app-staging
bundle exec rake spec:mon-staging
