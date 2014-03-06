#!/bin/bash 
set -e -u

# Now slow down. You might be wondering why we're doing something so patently
# insecure as replacing real entropy with fake entropy. We're doing this because
# travis VMs have very poor sources of real entropy 
# (see https://github.com/travis-ci/travis-ci/issues/1494), and we don't actually need
# securely random entropy for our automated tests. This craziness should never be done
# for a real installation.

# Based on: 
# https://github.com/travis-ci/travis-ci/issues/1495
# https://github.com/travis-ci/travis-ci/issues/1913#issuecomment-33891474

rm /dev/random
mknod -m 0666 /dev/random c 1 9

apt-get install rng-tools
rngd --random-device /dev/urandom --rng-device /dev/urandom
