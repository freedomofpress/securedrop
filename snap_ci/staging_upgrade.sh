#!/bin/bash
# The /staging/ snap-ci stage will:
# - Build new deb packages based on the environment variable BUILD_SKIP_TAGS
# - Using DO snapshots of the a clean install of the most recent tagged version
# used in production, will provision the /staging/ environment.
# - Will re-provision the /staging/ environment based on the STAGING_SKIP_TAGS
# environment variable.
#
# Requires the pinned commands to have already ran
# /bin/bash ./snap-ci/pinned.sh
# snap-wait 20 /bin/bash ./snap-ci/staging-upgrade.sh
#
# Snap-CI environment variables required
# - Ensure you use the Secure Variable option for the api token value.
# vagrant_rpm vagrant_1.7.2_x86_64.rpm
# DO_SSH_KEYFILE_NAME Vagrant
# DO_IMAGE_NAME {HOSTNAME}-{TAGGED-VERSION}
# DO_REGION nyc2
# DO_SIZE 1gb
# DEVELOPMENT_SKIP_TAGS mon_install_local_pkgs,aa-complain,grsec,sudoers
# DO_API_TOKEN ***
#
# Snap-CI Secure Files required:
# Owner Logical Name            File         Mode
# USER  snap_digital_ocean      /var/snap-ci/repo/id_rsa        0600
# USER  snap_digital_ocean.pub  /var/snap-ci/repo/id_rsa.pub    0600
# USER  staging-specific.yml
# /var/snap-ci/repo/install_files/ansible-base/staging-specific.yml 600
#
# The staging-specific.yml config file should have the sasl auth creds, OSSEC
# alert info, and use the following environment variables to populate the
# app and mon ip address.
# monitor_ip: "{{ lookup('env', 'APP_IP') }}"
# monitor_hostname: "mon-staging"
# app_hostname: "app-staging"
# app_ip: "{{ lookup('env', 'MON_IP') }}"


# Build new deb packages based on current repo
# The build vm does not get destroyed to save provisioning time.
# Up the droplet in case it was manually powered off/detroyed.
vagrant up build --no-provision
vagrant provision build

# The vagrant-digitalocean plugin uses a one way rsync to sync the /vagrant
# directory. The deb packages do not get synced back. SCP them from the
# build VM to the build dir in the repo. Configure that directory as an
# `Artifact` in snap-ci so the deb packages will be available to the other
# snap-ci stages.
# TODO: test for existence
ANSIBLE_INVENTORY='.vagrant/provisioners/ansible/inventory'
BUILD_IP=$(grep -r '^build' $ANSIBLE_INVENTORY | awk -F'[= ]' '{print $3}')
scp -r -i ./id_rsa vagrant@$BUILD_IP:/vagrant/build .

# If the previous pipleing failed the droplets wouldn't of been destroyed.
# Destroy them so you start with a clean tagged version from a snapshot.
vagrant destroy /staging/ -f

# Up the hosts separately so you can pass each droplet a specific image name as
# a var on cli. And so you can extract the DO dynamic IP address to use in the
# `staging-specific.yml` config before provisioning.
DO_IMAGE_NAME=$APP_IMAGE_NAME vagrant up app-staging --no-provision
DO_IMAGE_NAME=$MON_IMAGE_NAME vagrant up mon-staging --no-provision

# Register the ip addresses for app-staging and mon-staging vars to use in the
# staging-specific.yml.
# TODO: This will only work when direct access is enabled. Once the inventory
# file is switched to the tor onion addresses then this will be the wrong value
APP_IP=$(grep -r '^app-staging' $ANSIBLE_INVENTORY | awk -F'[= ]' '{print $3}')
echo "APP_IP" >> .env
MON_IP=$(grep -r '^mon-staging' $ANSIBLE_INVENTORY | awk -F'[= ]' '{print $3}')
echo "MON_IP" >> .env

echo $APP_IP
echo $MON_IP

# Provision the hosts in parallel
vagrant provision /staging/

# Run serverspec tests
cd /var/snap-ci/repo/spec_tests/
# TODO: Need to fix versioning mismatch of what is installed on snap-ci compared
# to tests. Commented out running serverspec tests till then.
#rake spec

# Destroy the droplets since you will want to start builds with a fresh tagged
# release and to save money.
vagrant destroy /staging/ -f
