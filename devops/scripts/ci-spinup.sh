#!/bin/bash
#
#
#
export RETRY_FILES_ENABLED="False"
export ANSIBLE_INVENTORY="localhost"

./devops/playbooks/aws-ci-startup.yml --diff

#testinfra --hosts=`cat jenkins-aws-instances` --junit-xml=junit.xml --sudo \
#    --ssh-config=/tmp/sshconfig-`echo $JOB_BASE_NAME | sed 's/\s//g'`$BUILD_NUMBER
