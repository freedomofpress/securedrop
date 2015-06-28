#!/bin/bash

# bail out on errors
set -e
set -x

# declare function for EXIT trap
function cleanup {
    echo "Destroying droplet..."
    vagrant destroy /prod/ -f
}

# Ensure that DigitalOcean droplet will be cleaned up
# even if script errors (e.g., if serverspec tests fail).
trap cleanup EXIT

# If the previous build in snap-ci failed, the droplet
# will still exist. Ensure that it's gone with a pre-emptive destroy.
cleanup

repo_root=$( cd "$( dirname $( dirname "${BASH_SOURCE[0]}" )  )" && pwd  )
# Copy staging vars for use as prod vars; will need to skip "validate" role.
sed -r -e 's/(app|mon)-staging/\1-prod/' \
    "${repo_root}"/install_files/ansible-base/staging-specific.yml > \
    "${repo_root}"/install_files/ansible-base/prod-specific.yml
export PROD_SKIP_TAGS=validate,grsec

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up /prod/ --no-provision --provider digital_ocean

# Run only the shell provisioner, to ensure the "vagrant"
# user account exists with nopasswd sudo.
vagrant provision /prod/ --provision-with shell
vagrant provision /prod/ --provision-with ansible


# Surprisingly, "ansible" allows process substitution for inventory files,
# but "ansible-playbook" doesn't. Looks like DeHaan never thought of it:
# https://groups.google.com/forum/#!msg/ansible-project/MxTAXibLNy8/SWoDn-LXZrYJ
# Probably due to some +x and type:file checking for dynamic inventories,
# accidentally breaking FIFO pipes. So, create a tempfile instead.
inventory_file=$(mktemp)

# prod playbook reboots servers as final task,
# so give them time to come back up. configure
# tor on test node while servers boot.
ansible-playbook -i $inventory_file -c local -s "${repo_root}/install_files/ansible-base/securedrop-snapci.yml"

# prod playbooks restrict ssh access to tor aths,
# so tell vagrant to read aths values for ssh-config
export SECUREDROP_SSH_OVER_TOR=1
# shouldn't be necessary to provision again...
# the apache default web dir may be present and cause
# a test to fail.
#
# vagrant provision /prod/ --provision-with ansible

# Run serverspec tests
cd "${repo_root}/spec_tests/"
bundle exec rake spec:app-prod
bundle exec rake spec:mon-prod
