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

    return hostvars


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
