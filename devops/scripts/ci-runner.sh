#!/bin/bash -e
# shellcheck disable=SC2016

. devops/ansible_env
# Make sure CI teardown gets run on error
trap "make ci-teardown" ERR

# Set hostnames for CI boxes based on inventory names
ansible staging -b -m hostname -a "name={{inventory_hostname}}"

# Hotfix for missing hostname attached to localhost
ansible staging -b -m lineinfile -a "dest=/etc/hosts line='127.0.0.1 localhost {{inventory_hostname}}' regexp='^127\.0\.0\.1'"

SSH_USER="$(whoami)"
if [[ "${SSH_USER}" == 'root' ]]; then SSH_USER='ubuntu'; fi

# Build + install packages, install securedrop, and configure servers
ansible-playbook "install_files/ansible-base/securedrop-${CI_SD_ENV}.yml" --skip-tags="grsec,local_build" -e primary_network_iface=eth0 -e install_local_packages=true -e ssh_users="${SSH_USER}"

# Reboot and wait
./devops/playbooks/reboot_and_wait.yml --diff
