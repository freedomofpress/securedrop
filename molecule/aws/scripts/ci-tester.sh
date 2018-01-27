#!/bin/bash -e
# shellcheck disable=SC2016
#
#
if [ "$?" == "0" ]; then
    case "$CI_SD_ENV" in
    "staging")
        ./testinfra/test.py "app-$CI_SD_ENV" || export TEST_FAIL=true
        ./testinfra/test.py "mon-$CI_SD_ENV" || export TEST_FAIL=true
        ./testinfra/test.py staging || export TEST_FAIL=true
        ;;
    esac
fi

if [ "${TEST_FAIL}" == "true" ]; then exit 1; fi
