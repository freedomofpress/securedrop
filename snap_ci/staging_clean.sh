#!/bin/bash
set -e
set -x

# Find the root of the git repository. A simpler implementation
# would be `git rev-parse --show-toplevel`, but that must be run
# from inside the git repository, whereas the solution below is
# directory agnostic. Exporting this variable doesn't work in snapci,
# so it must be rerun in each stage.
repo_root=$( dirname "$( cd "$( dirname "${BASH_SOURCE[0]}"  )" && pwd )" )

# Respect environment variables, but default to VirtualBox.
VAGRANT_DEFAULT_PROVIDER="${VAGRANT_DEFAULT_PROVIDER:-virtualbox}"

# Only enable auto-destroy for testing droplets
# if we're running in Snap-CI. If not running in Snap-CI,
# then executing this bash script will run all the tests
# locally.
if [[ "${SNAP_CI}" == "true" ]]; then
    # declare function for EXIT trap
    function cleanup {
        echo "Destroying droplet..."
        vagrant destroy build /staging/ -f
    }
    # Ensure that DigitalOcean droplet will be cleaned up
    # even if script errors (e.g., if serverspec tests fail).
    trap cleanup EXIT
    # If the previous build in snap-ci failed, the droplet
    # will still exist. Ensure that it's gone with a pre-emptive destroy.
    cleanup

    # Force DigitalOcean testing in Snap-CI.
    VAGRANT_DEFAULT_PROVIDER="digital_ocean"

    # Snap-CI does not allow large files for uploads in build stages. For local development,
    # the OSSEC packages should be built in the "ossec" repo and copied into the "build" directory.
    # Since these deb files seldom change, it's OK to pull them down for each build.
    # Certainly faster than building unchanged files repeatedly.
    wget http://apt.freedom.press/pool/main/o/ossec.net/ossec-server-2.8.2-amd64.deb \
        --continue --output-document "${repo_root}/build/ossec-server-2.8.2-amd64.deb"
    wget http://apt.freedom.press/pool/main/o/ossec.net/ossec-agent-2.8.2-amd64.deb \
        --continue --output-document "${repo_root}/build/ossec-agent-2.8.2-amd64.deb"

    # The Snap-CI nodes run CentOS, and so have an old version of rsync that doesn't support
    # --chown or --usermap, one of which is required for the build-debian-package role in staging.
    rsync_rpm="rsync-3.1.0-1.el6.rfx.x86_64.rpm"
    rsync_url="http://pkgs.repoforge.org/rsync/${rsync_rpm}"
    [[ -f "${tmp_dir}/${rsync_rpm}" ]] || wget -q "$rsync_url" -O "${tmp_dir}/${rsync_rpm}"
    sudo -E rpm -U --force -vh "${tmp_dir}/${rsync_rpm}"
fi

# Make sure the environment variable is available
# to additional tasks in the testing environment.
export VAGRANT_DEFAULT_PROVIDER

if [[ "${VAGRANT_DEFAULT_PROVIDER}" == "digital_ocean" ]] ; then
    # Skip "grsec" because DigitalOcean Ubuntu 14.04 hosts don't support custom kernels.
    export ANSIBLE_ARGS="--skip-tags=grsec"
fi

# Create target hosts, but don't provision them yet. The shell provisioner
# is only necessary for DigitalOcean hosts, and must run as a separate task
# from the Ansible provisioner, otherwise it will only run on one of the two
# hosts, due to the `ansible.limit = 'all'` setting in the Vagrantfile.
vagrant up build /staging/ --no-provision --provider "${VAGRANT_DEFAULT_PROVIDER}"

# First run only the shell provisioner, to ensure the "vagrant"
# user account exists with nopasswd sudo, then run Ansible.
# Only matters for droplets; no-op for VirtualBox hosts.
vagrant provision build /staging/ --provision-with shell
vagrant provision /staging/ --provision-with ansible

# Reload required to apply iptables rules.
vagrant reload /staging/
sleep 30 # wait for servers to come back up

# Run serverspec tests
cd "${repo_root}/spec_tests/"
bundle exec rake spec:build
bundle exec rake spec:app-staging
bundle exec rake spec:mon-staging
