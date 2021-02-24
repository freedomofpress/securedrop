"""
Configuration for TestInfra test suite for SecureDrop.
Handles importing host-specific test vars, so test functions
can be reused across multiple hosts, with varied targets.

Vars should be placed in `testinfra/vars/<hostname>.yml`.
"""

import io
import os
import yaml
from typing import Any, Dict

import testutils


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

    # Testing against both Focal and Xenial must be supported for now in both
    # staging scenarios, and in prod via `USE_FOCAL=1 ./securedrop-admin verify`
    testing_focal = False
    scenario_env = "MOLECULE_SCENARIO_NAME"
    if scenario_env in os.environ and os.environ.get(scenario_env).endswith("focal"):
        testing_focal = True
    if "USE_FOCAL" in os.environ:
        testing_focal = True

    if testing_focal:
        hostvars['securedrop_venv_site_packages'] = hostvars["securedrop_venv_site_packages"].format("3.8")  # noqa: E501
        hostvars['python_version'] = "3.8"
    else:
        hostvars['securedrop_venv_site_packages'] = hostvars["securedrop_venv_site_packages"].format("3.5")  # noqa: E501
        hostvars['python_version'] = "3.5"

    if with_header:
        hostvars = dict(securedrop_test_vars=hostvars)

    return hostvars


class TestVars(dict):
    managed_attrs = {}  # type: Dict[str, Any]

    def __init__(self, initial: Dict[str, Any]) -> None:
        self.securedrop_target_distribution = os.environ.get("SECUREDROP_TARGET_DISTRIBUTION")
        self.managed_attrs.update(initial)

    def __getattr__(self, name: str) -> Any:
        """
        If the requested attribute names a dict in managed_attrs and that
        contains a key with the name of the target distribution,
        e.g. "focal", return that. Otherwise return the entire item
        under the requested name.
        """
        try:
            attr = self.managed_attrs[name]
            if isinstance(attr, dict) and self.securedrop_target_distribution in attr:
                return attr[self.securedrop_target_distribution]
            return attr
        except KeyError:
            raise AttributeError(name)

    def __str__(self) -> str:
        return str(self.managed_attrs)


testutils.securedrop_test_vars = TestVars(securedrop_import_testinfra_vars(target_host))
