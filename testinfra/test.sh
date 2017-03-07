#!/bin/bash
set -e
set -x


# Hard-coding the development VM during migration from Serverspec -> Testinfra.
#if [[ $# -lt 1 ]]; then
#    echo "Usage: $0 <host>"
#    exit 1
#fi

target_host=${1:development}
#shift 1

testinfra \
    -v \
    --connection ansible \
    --ansible-inventory .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    --hosts "${target_host}" \
    testinfra/development \
    testinfra/app-code \
    testinfra/mon\
    ${@:2}
