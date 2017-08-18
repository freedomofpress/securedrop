#!/bin/bash -x
#
#
#
. devops/ansible_env
devops/scripts/docs-detection || exit 0

export ANSIBLE_INVENTORY="localhost"
export RETRY_FILES_ENABLED=False

if [ ! -f "$HOME/.FPF_CI_DEBUG" ]; then
    ./devops/playbooks/aws-ci-teardown.yml --diff
fi
