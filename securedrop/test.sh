#!/bin/bash

if [ $(which vagrant) ] ; then
    echo ""
    echo "*** You probably want to run tests from vagrant. Run 'vagrant ssh', then 'cd /vagrant/securedrop' and re-run this script***"
    echo ""
fi

export PYTHONPATH=./tests

# -f makes unittest fail fast, so we can use && to avoid burying test failures
python -m unittest discover ./tests/unit_tests/ -fv -p 'test_*.py' && python -m unittest -fv tests.test_integration && python -m unittest -fv tests.functional.submit_and_retrieve_message && python -m unittest -fv tests.functional.submit_and_retrieve_file


