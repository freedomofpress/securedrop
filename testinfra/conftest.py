"""
Configuration for TestInfra test suite for SecureDrop.
Handles importing host-specific test vars, so test functions
can be reused across multiple hosts, with varied targets.

Vars should be placed in `testinfra/vars/<hostname>.yml`.
"""

import os
import yaml


target_host = os.environ['SECUREDROP_TESTINFRA_TARGET_HOST']
assert target_host != ""


def securedrop_import_testinfra_vars(hostname, with_header=False):
    """
    Import vars from a YAML file to populate tests with host-specific
    values used in checks. For instance, the SecureDrop docroot will
    be under /vagrant in development, but /var/www/securedrop in staging.

    Vars must be stored in `testinfra/vars/<hostname>.yml`.
    """
    filepath = os.path.join(os.path.dirname(__file__), "vars", hostname+".yml")
    with open(filepath, 'r') as f:
        hostvars = yaml.safe_load(f)
    # The directory Travis runs builds in varies by PR, so we cannot hardcode
    # it in the YAML testvars. Read it from env var and concatenate.
    if hostname.lower() == 'travis':
        build_env = os.environ["TRAVIS_BUILD_DIR"]
        hostvars['securedrop_code'] = build_env+"/securedrop"

    if with_header:
        hostvars = dict(securedrop_test_vars=hostvars)
    return hostvars


def pytest_namespace():
    return securedrop_import_testinfra_vars(target_host, with_header=True)
