#!/bin/bash
# Pin commands to install vagrant, ansible, serverspec
# Pinning commands will ensure that they are run in each snap-ci stage.
# This is useful for two reasons:
#   * rerunning a single stage from a pipeline of many
#   * keeping the CI suite DRY

set -e
set -x

# TODO: temporarily set different zone due to digitalocean SFO1 issues
export DO_REGION=nyc2

# Find the root of the git repository. A simpler implementation
# would be `git rev-parse --show-toplevel`, but that must be run
# from inside the git repository, whereas the solution below is
# directory agnostic.
export repo_root=$( dirname "$( cd "$( dirname "${BASH_SOURCE[0]}"  )" && pwd )" )

# Support Snap-CI cache directory, but also allow this script to be run locally.
export tmp_dir="${SNAP_CACHE_DIR:-/tmp}"

# Cache and install Vagrant
vagrant_rpm="${vagrant_rpm:-vagrant_1.7.2_x86_64.rpm}"
[[ -f ${SNAP_CACHE_DIR}/$vagrant_rpm ]] || wget https://dl.bintray.com/mitchellh/vagrant/$vagrant_rpm -O ${SNAP_CACHE_DIR}/$vagrant_rpm
[[ -x /usr/bin/vagrant ]] || sudo -E rpm -ivh ${SNAP_CACHE_DIR}/$vagrant_rpm
# TODO: Check for vagrant plugins before installing them.

# An older version of digital_ocean plugin is used because of an issue with the
# current version that doesn't support using snapshots.
# https://github.com/smdahlen/vagrant-digitalocean/issues/187
#/usr/bin/vagrant plugin install vagrant-digitalocean --plugin-version '0.7.0'
/usr/bin/vagrant plugin install vagrant-digitalocean

vagrant plugin install vagrant-hostmanager
[[ -f ${SNAP_CACHE_DIR}/digital_ocean.box ]] || wget https://github.com/smdahlen/vagrant-digitalocean/raw/master/box/digital_ocean.box -O ${SNAP_CACHE_DIR}/digital_ocean.box
# TODO: Check to see if the box was already added before doing again.
vagrant box add digital_ocean ${SNAP_CACHE_DIR}/digital_ocean.box --force

# Install Ansible dependencies
sudo yum install python-pip
# Install Ansible via pip for fine-grained version control
sudo pip install ansible==1.9.0.1

# Install serverspec dependencies
cd "${repo_root}/spec_tests/" && bundle install
