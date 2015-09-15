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

# Find the root of the git repository. A simpler implementation
# would be `git rev-parse --show-toplevel`, but that must be run
# from inside the git repository, whereas the solution below is
# directory agnostic. Exporting this variable doesn't work in snapci,
# so it must be rerun in each stage.
repo_root=$( dirname "$( cd "$( dirname "${BASH_SOURCE[0]}"  )" && pwd )" )

# Copy staging vars for use as prod vars; will need to skip "validate" role.
# Staging config includes looser Apache rules, so filter those out.
sed -r -e 's/(app|mon)-staging/\1-prod/' \
    "${repo_root}"/install_files/ansible-base/group_vars/staging.yml | \
    grep -vi apache > \
    "${repo_root}"/install_files/ansible-base/prod-specific.yml

# Skip "validate" so reused vars don't cause failure,
# and skip "grsec" because DigitalOcean hosts don't support custom kernels.
export SECUREDROP_PROD_SKIP_TAGS=validate,grsec

# Assume that /prod/ instances will be created from scratch, as part
# of a full provisioning run, so initial SSH connections must be
# made directly, rather than over Tor.
unset SECUREDROP_SSH_OVER_TOR

# Create target hosts, but don't provision them yet. The shell provisioner
# is only necessary for DigitalOcean hosts, and must run as a separate task
# from the Ansible provisioner, otherwise it will only run on one of the two
# hosts, due to the `ansible.limit = 'all'` setting in the Vagrantfile.
vagrant up /prod/ --no-provision --provider digital_ocean

# First run only the shell provisioner, to ensure the "vagrant"
# user account exists with nopasswd sudo, then run Ansible.
vagrant provision /prod/ --provision-with shell
vagrant provision /prod/ --provision-with ansible

# Surprisingly, "ansible" allows process substitution for inventory files,
# but "ansible-playbook" doesn't. Looks like DeHaan never thought of it:
# https://groups.google.com/forum/#!msg/ansible-project/MxTAXibLNy8/SWoDn-LXZrYJ
# Probably due to some +x and type:file checking for dynamic inventories,
# accidentally breaking FIFO pipes. So, create a tempfile instead.
inventory_file=$(mktemp)
echo "snapci ansible_ssh_host=localhost" > "$inventory_file"

# The prod playbook reboots servers as the final task,
# so give them time to come back up. While servers boot,
# configure Tor on the snapci test node.
ansible-playbook -i $inventory_file -c local -s "${repo_root}/install_files/ansible-base/securedrop-snapci.yml" -vv
# Ad-hoc testing shows that the above playbook run isn't
# nearly enough time for a reboot and Tor connection to bootstrap,
# so sleep for another few minutes.
sleep 300

# The prod playbook restricts SSH access to Tor ATHS,
# so tell Vagrant to read ATHS values for ssh-config.
export SECUREDROP_SSH_OVER_TOR=1

# It shouldn't be necessary to provision again, since the
# prod playbooks reboot again. In the staging environment,
# a second provision run ensures removal of /var/www/html,
# but a second provision run on prod would take forever, so
# that spectest is temporarily disabled.
# vagrant provision /prod/ --provision-with ansible

# Run serverspec tests
cd "${repo_root}/spec_tests/"
bundle exec rake spec:app-prod
bundle exec rake spec:mon-prod
