#!/usr/bin/env python
"""
Wrapper script for running Testinfra against SecureDrop VMs.
Accepts a single argument: the hostname to run the tests against.
Script will handle building the list of tests to run, based on hostname.
"""
import os
import subprocess
import sys
import tempfile

# By default let's assume we're testing against the development VM.
try:
    target_host = sys.argv[1]
except IndexError:
    target_host = "development"

# Set env var so that `testinfra/conftest.py` can read in a YAML vars file
# specific to the host being tested.
os.environ['SECUREDROP_TESTINFRA_TARGET_HOST'] = target_host


def get_target_roles(target_host):
    """
    Assemble list of role tests to run. Hard-coded per host.
    """
    target_roles = {"development": ['testinfra/app-code',
                                    'testinfra/development'],
                    "app-staging": ['testinfra/app',
                                    'testinfra/app-code',
                                    'testinfra/common',
                                    'testinfra/development/test_xvfb.py'],
                    "mon-staging": ['testinfra/mon',
                                    'testinfra/common'],
                    "mon-prod":    ['testinfra/mon']}

    try:
        return target_roles[target_host]
    except KeyError:
        print("Unknown host '{}'! Exiting.".format(target_host))
        sys.exit(1)


def run_testinfra(target_host, verbose=True):
    """
    Handler for executing testinfra against `target_host`.
    Queries list of roles via helper def `get_target_roles`.
    """
    conn_type = "ssh"
    target_roles = get_target_roles(target_host)
    if verbose:
        # Print informative output prior to test run.
        print("Running Testinfra suite against '{}'...".format(target_host))
        print("Target roles:")
        for role in target_roles:
            print("    - {}".format(role))

    # Prod hosts host have SSH access over Tor. Let's use the SSH backend
    # for Testinfra, rather than Ansible. When we write a dynamic inventory
    # script for Ansible SSH-over-Tor, we can use the Ansible backend
    # everywhere.
    if target_host.endswith("-prod"):
        os.environ['SECUREDROP_SSH_OVER_TOR'] = '1'
        # Dump SSH config to tempfile so it can be passed as arg to testinfra.
        ssh_config_output = subprocess.check_output(["vagrant", "ssh-config",
                                                     target_host])
        # Create temporary file to store ssh-config. Not deleting it
        # automatically because there's no sensitive info (HidServAuth is
        # required to connect), and we'll need it outside of the
        # context-manager block that writes to it.
        ssh_config_tmpfile = tempfile.NamedTemporaryFile(delete=False)
        with ssh_config_tmpfile.file as f:
            f.write(ssh_config_output)
        ssh_config_path = ssh_config_tmpfile.name
        testinfra_command_template = """
testinfra \
    -vv \
    -n auto \
    --connection ssh \
    --ssh-config \
    {ssh_config_path}\
    --hosts {target_host} \
    {target_roles}
""".lstrip().rstrip()

    elif os.environ.get("FPF_CI", 'false') == 'true':
        if os.environ.get("CI_SD_ENV", "development") == "development":
            os.environ['SECUREDROP_TESTINFRA_TARGET_HOST'] = "travis"
            ssh_config_path = ""
            testinfra_command_template = "testinfra -vv {target_roles}"
        else:
            ssh_config_path = os.environ["CI_SSH_CONFIG"]
            testinfra_command_template = """
testinfra \
    -vv \
    -n 8 \
    --connection {connection_type} \
    --ssh-config \
    {ssh_config_path}\
    --junit-xml=./{target_host}-results.xml\
    --junit-prefix={target_host}\
    --hosts {target_host} \
    {target_roles}
""".lstrip().rstrip()

    else:
        ssh_config_path = ""
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
            ssh_config_path=ssh_config_path,
            connection_type=conn_type,
            target_roles=" ".join(target_roles),
            ).split()

    # Execute config tests.
    subprocess.check_call(testinfra_command)


if __name__ == "__main__":
    run_testinfra(target_host)
