#!/bin/bash -e

. devops/ansible_env

# Ensure docker build image is loaded
./devops/playbooks/aws-ci-startup.yml -t docker

# Build + install packages, install securedrop, and configure servers
ansible-playbook "install_files/ansible-base/securedrop-${CI_SD_ENV}.yml" -l build -t build_debs
