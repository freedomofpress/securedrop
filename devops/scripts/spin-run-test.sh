#!/bin/bash -e
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

# Run tests
./devops/scripts/ci-tester.sh
