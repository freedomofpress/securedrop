"""
Configuration for TestInfra test suite for SecureDrop.
Handles importing host-specific test vars, so test functions
can be reused across multiple hosts, with varied targets.

Vars should be placed in `testinfra/vars/<hostname>.yml`.
"""

import io
import os
import yaml


# The config tests target staging by default. It's possible to override
# for e.g. prod, but the associated vars files are not yet ported.
target_host = os.environ.get('SECUREDROP_TESTINFRA_TARGET_HOST', 'staging')


def securedrop_import_testinfra_vars(hostname, with_header=False):
    """
    Import vars from a YAML file to populate tests with host-specific
    values used in checks. For instance, the SecureDrop docroot will
    be under /vagrant in development, but /var/www/securedrop in staging.

    Vars must be stored in `testinfra/vars/<hostname>.yml`.
    """
    filepath = os.path.join(os.path.dirname(__file__), "vars", hostname+".yml")
    with io.open(filepath, 'r') as f:
        hostvars = yaml.safe_load(f)

    if with_header:
        hostvars = dict(securedrop_test_vars=hostvars)

    if os.environ.get("FPF_CI", False):
        export_ci_var_overrides()

    return hostvars


def export_ci_var_overrides():
    """
    In CI environments, the hardcoded local IP addresses aren't valid
    (since we're testing against remote AWS hosts). Detect the CI env,
    and look up the proper IPs for use in the testinfra tests.
    Expose those IPs as environment variables, so the tests can use them.
    """
    molecule_info = lookup_molecule_info()
    app_ip = lookup_aws_private_address(molecule_info, 'app-staging')
    mon_ip = lookup_aws_private_address(molecule_info, 'mon-staging')

    os.environ['APP_IP'] = app_ip
    os.environ['MON_IP'] = mon_ip

    # Make SSH calls more resilient, as we're operating against remote hosts,
    # and running from CI. We've observed flakey connections in CI at times.
    os.environ['ANSIBLE_SSH_RETRIES'] = '5'
    ssh_args = [
        "-o ConnectTimeout=60s",
        "-o ControlMaster=auto",
        "-o ControlPersist=180s",
        "-o StrictHostKeyChecking=no",
    ]
    os.environ['ANSIBLE_SSH_ARGS'] = " ".join(ssh_args)


def lookup_aws_private_address(molecule_info, hostname):
    """
    Inspect Molecule instance config dict (imported from YAML file),
    and return the attribute for the requested hostname.
    """

    host_info = list(filter(lambda x: x['instance'] == hostname,
                            molecule_info))[0]
    host_ip = host_info['priv_address']
    return host_ip


def lookup_molecule_info():
    """
    Molecule automatically writes YAML files documenting dynamic host info
    such as remote IPs. Read that file and pass back the config dict.
    """
    molecule_instance_config_path = os.path.abspath(
            os.environ['MOLECULE_INSTANCE_CONFIG'])
    with open(molecule_instance_config_path, 'r') as f:
        molecule_instance_config = yaml.safe_load(f)
    return molecule_instance_config


def pytest_namespace():
    return securedrop_import_testinfra_vars(target_host, with_header=True)
