#!/bin/bash

if [ $(which vagrant) ] ; then
    echo ""
    echo "*** You probably want to run tests from vagrant. Run 'vagrant ssh', then 'cd /vagrant/securedrop' and re-run this script***"
    echo ""
fi

export PYTHONPATH=./tests

# -f makes unittest fail fast, so we can use && to avoid burying test failures
python -m unittest discover -t . -s ./tests/unit_tests/ -fv -p 'test_*.py' && python -m unittest discover -t . -s ./tests/functional -fv -p 'test_*.py'


