#!/bin/bash
# Pin commands to install vagrant, ansible, serverspec
# Pinning commands will ensure that they are run in each snap-ci stage.
# This is useful for two reasons:
#   * rerunning a single stage from a pipeline of many
#   * keeping the CI suite DRY


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
cd /var/snap-ci/repo/spec_tests/ && bundle update
