#!/bin/bash -e
# shellcheck disable=SC2016
#
#
if [ "$?" == "0" ]; then
    case "$CI_SD_ENV" in
    "staging")
        ./testinfra/test.py "app-$CI_SD_ENV" || true
        ./testinfra/test.py "mon-$CI_SD_ENV" || true
        ./testinfra/test.py apptestclient || true
        ;;
    "development")
        ./testinfra/test.py development
        ;;
    esac
fi

# Remove any existing result files
rm -r "./junit" || true
mkdir "./junit" || true

./testinfra/combine-junit.py ./*results.xml > "./junit/junit.xml"
