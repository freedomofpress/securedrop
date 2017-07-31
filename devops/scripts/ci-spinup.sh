#!/bin/bash
#
#
#
. devops/ansible_env
trap "make ci-teardown" ERR

./devops/playbooks/aws-ci-startup.yml --diff
