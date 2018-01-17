#!/bin/bash
# shellcheck disable=SC2162,SC2034
#
set -a
FPF_CI=true

read -e -p "Enter a build designator: " -i "${USER}" CIRCLE_BUILD_NUM
read -e -p "Enter AWS region: " -i "us-west-1" CI_AWS_REGION
read -e -p "Enter AWS EC2 type: " -i "t2.small" CI_AWS_TYPE
read -e -p "Enter CI SD environment type: " -i "staging" CI_SD_ENV
read -e -p "Run GRSEC tests? " -i "false" FPF_GRSEC
