#!/usr/bin/env python
"""
Wrapper script for running Testinfra against SecureDrop VMs.
Accepts a single argument: the hostname to run the tests against.
Script will handle building the list of tests to run, based on hostname.
"""
import os
import subprocess
import sys

# By default let's assume we're testing against the development VM.
try:
    target_host = sys.argv[1]
except IndexError:
    target_host = "development"

# Set env var so that `testinfra/conftest.py` can read in a YAML vars file
# specific to the host being tested.
os.environ['SECUREDROP_TESTINFRA_TARGET_HOST'] = target_host

# Assemble list of role tests to run. Hard-coded per host.
if target_host == "development":
    target_roles = [
            'testinfra/app-code',
            'testinfra/development',
            ]

elif target_host == "app-staging":
    target_roles = [
            'testinfra/app',
            'testinfra/app-code',
            'testinfra/common',
            'testinfra/development/test_xvfb.py',
            ]

elif target_host == "mon-staging":
    target_roles = [
            'testinfra/mon',
            'testinfra/common',
            ]

elif target_host == "mon-prod":
    target_roles = [
            'testinfra/mon',
            ]

elif target_host == "build":
    target_roles = [
            'testinfra/build',
            ]
else:
    print("Unknown host '{}'! Exiting.".format(target_host))
    sys.exit(1)


# Print informative output prior to test run.
print("Running Testinfra suite against '{}'...".format(target_host))
print("Target roles:")
for role in target_roles:
    print("    - {}".format(role))


# Execute config tests.
testinfra_command_template = """
testinfra \
    -vv \
    -n auto \
    --connection ansible \
    --ansible-inventory \
    .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    --hosts {target_host} \
    {target_roles}
""".lstrip().rstrip()

testinfra_command = testinfra_command_template.format(
        target_host=target_host,
        target_roles=" ".join(target_roles),
        ).split()

subprocess.check_call(testinfra_command)
