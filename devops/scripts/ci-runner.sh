#!/bin/bash

. devops/ansible_env
# Make sure CI teardown gets run on error
trap "make ci-teardown" ERR

# Set hostnames for CI boxes based on inventory names
ansible staging -b -m hostname -a "name={{inventory_hostname}}"

# Hotfix for missing hostname attached to localhost
ansible staging -b -m lineinfile -a "dest=/etc/hosts line='127.0.0.1 localhost {{inventory_hostname}}' regexp='^127\.0\.0\.1'"


# Build OSSEC agent+server packages
ansible-playbook install_files/ossec-packages/ansible/build-deb-pkgs.yml -e build_path=/tmp/ossec-build -e repo_src_path="/tmp/ossec-src" -e local_build_path="../../../build/"

# Build + install OSSEC config packages, install securedrop
ansible-playbook install_files/ansible-base/securedrop-${CI_SD_ENV}.yml --skip-tags="grsec,local_build" -e primary_network_iface=eth0 -e install_local_packages=true -e ssh_users="$USER"

# Reboot and wait
./devops/playbooks/reboot_and_wait.yml --diff
