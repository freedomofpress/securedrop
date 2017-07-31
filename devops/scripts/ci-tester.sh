#!/bin/bash -e
# shellcheck disable=SC2016
#
#
. devops/ansible_env
trap "make ci-teardown" ERR

# Quick hack to pass IPs off to testinfra
for host in app mon; do
    # tacking xargs at the end strips the trailing space
    ip=$(ssh -F "$HOME/.ssh/sshconfig-securedrop-ci-$BUILD_NUM" "${host}-$CI_SD_ENV" "hostname -I" | xargs)
    ansible -c local localhost -m lineinfile -a "dest=./testinfra/vars/app-${CI_SD_ENV}.yml line='${host}_ip: $ip' regexp='^${host}_ip'" > /dev/null
    ansible -c local localhost -m lineinfile -a "dest=./testinfra/vars/mon-${CI_SD_ENV}.yml line='${host}_ip: $ip' regexp='^${host}_ip'" > /dev/null
done

# Ensure we can SSH to both hosts before kicking off tests
ansible staging -m ping > /dev/null || exit 1

# Cleanup any possible lingering previous results
rm -v ./*results.xml || true

if [ "$?" == "0" ]; then
    case "$CI_SD_ENV" in
    "staging")
        ./testinfra/test.py build
        ./testinfra/test.py "app-$CI_SD_ENV"
        ./testinfra/test.py "mon-$CI_SD_ENV"
        ./testinfra/test.py apptestclient
        ;;
    "development")
        ./testinfra/test.py development
        ;;
    esac
fi

# Run application tests
./devops/playbooks/ci-app-tests.yml

if [[ -z "${TEST_REPORTS}" ]] || [[ "${TEST_REPORTS}" == '${CIRCLE_TEST_REPORTS}' ]]; then
    TEST_REPORTS=$(pwd)
    export TEST_REPORTS
fi

# Remove any existing result files
rm -r "$TEST_REPORTS/junit" || true
mkdir "$TEST_REPORTS/junit" || true

./testinfra/combine-junit.py ./*results.xml > "$TEST_REPORTS/junit/junit.xml"
