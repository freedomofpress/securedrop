#!/bin/bash
#
#
#
. devops/ansible_env

# When this script completes, teardown the environment
# To get around this and debug, enter `make ci-debug` before
# or during execution.


# Only run test task (usually used in local testing)
if [ ! "$1" == "only_test" ]; then
    make ci-spinup && make ci-run
fi

# Quick hack to pass IPs off to testinfra
for host in app mon; do
    # tacking xargs at the end strips the trailing space
    ip=`ssh -F $HOME/.ssh/sshconfig-securedrop-ci-$BUILD_NUM ${host}-$CI_SD_ENV "hostname -I" | xargs`
    ansible -c local localhost -m lineinfile -a "dest=./testinfra/vars/app-${CI_SD_ENV}.yml line='${host}_ip: $ip' regexp='^${host}_ip'"
    ansible -c local localhost -m lineinfile -a "dest=./testinfra/vars/mon-${CI_SD_ENV}.yml line='${host}_ip: $ip' regexp='^${host}_ip'"
done

# Ensure we can SSH to both hosts before kicking off tests
ansible staging -m ping || exit 1

# Cleanup any possible lingering previous results
rm -v *results.xml || true

if [ "$?" == "0" ]; then
    case "$CI_SD_ENV" in
    "staging")
        ./testinfra/test.py app-$CI_SD_ENV
        ./testinfra/test.py mon-$CI_SD_ENV
        ;;
    "development")
        ./testinfra/test.py development
        ;;
    esac
fi

if [ -z "$TEST_REPORTS" ]; then
    export TEST_REPORTS=`pwd`
fi

# Remove any existing result files
rm -r $TEST_REPORTS/junit || true
mkdir $TEST_REPORTS/junit || true

./testinfra/combine-junit.py *results.xml > $TEST_REPORTS/junit/junit.xml
