#!/bin/bash

if [ $(which vagrant) ] ; then
    echo ""
    echo "*** You probably want to run tests from vagrant. Run 'vagrant ssh', then 'cd /vagrant/securedrop' and re-run this script***"
    echo ""
fi

export PYTHONPATH=./tests
export SECUREDROP_ENV=test

# -f makes unittest fail fast, so we can use && to avoid burying test failures
python -m unittest -fv tests.functional.submit_and_retrieve_message && \
python -m unittest -fv tests.functional.submit_and_retrieve_file && \
python -m unittest -fv tests.functional.admin_interface && \
python -m unittest -fv tests.functional.tagging_of_sources_and_submissions
