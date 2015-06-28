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
#trap cleanup EXIT

# If the previous build in snap-ci failed, the droplet
# will still exist. Ensure that it's gone with a pre-emptive destroy.
#cleanup

repo_root=$( cd "$( dirname $( dirname "${BASH_SOURCE[0]}" )  )" && pwd  )
cp "${repo_root}"/install_files/ansible-base/{staging,prod}-specific.yml
sed -i -e 's/app-staging/app-prod/g' "${repo_root}/install_files/ansible-base/prod-specific.yml"
sed -i -e 's/mon-staging/mon-prod/g' "${repo_root}/install_files/ansible-base/prod-specific.yml"
export PROD_SKIP_TAGS=validate,grsec

# Up the host in a separate command to avoid snap-ci command timeouts.
vagrant up /prod/ --no-provision --provider digital_ocean

# Run only the shell provisioner, to ensure the "vagrant"
# user account exists with nopasswd sudo.
vagrant provision /prod/ --provision-with shell
vagrant provision /prod/ --provision-with ansible

# prod playbook reboots servers as final task
sleep 180 # wait for servers to come back up
# prod playbooks restrict ssh access to tor aths,
# so tell vagrant to read aths values for ssh-config
export SECUREDROP_TOR_OVER_SSH=1
vagrant provision /prod/ --provision-with ansible

# Run serverspec tests
#cd /var/snap-ci/repo/spec_tests/
cd spec_tests/
bundle exec rake spec:app-prod
bundle exec rake spec:mon-prod
