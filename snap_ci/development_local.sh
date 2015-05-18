#!/bin/bash

# bail out on errors
set -e
# configure local ansible environment
echo localhost > inventory
ansible-playbook -i inventory --syntax-check install_files/ansible-base/securedrop-travis.yml
ansible-playbook -i inventory --connection=local --sudo --skip-tags=non-development install_files/ansible-base/securedrop-travis.yml

# Using 0<&- to close STDIN based on advice here:
# https://docs.snap-ci.com/troubleshooting/#my-build-is-timing-out
export DISPLAY=:1; cd /var/snap-ci/repo/securedrop && ./manage.py test  0<&-
