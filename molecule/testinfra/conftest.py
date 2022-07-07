"""
Configuration for TestInfra test suite for SecureDrop.
Handles importing host-specific test vars, so test functions
can be reused across multiple hosts, with varied targets.

Vars should be placed in `testinfra/vars/<hostname>.yml`.
"""

import io
import os
from typing import Any, Dict

import testutils
import yaml

# The config tests target staging by default.
target_host = os.environ.get("SECUREDROP_TESTINFRA_TARGET_HOST", "staging")


def securedrop_import_testinfra_vars(hostname, with_header=False):
    """
    Import vars from a YAML file to populate tests with host-specific
    values used in checks. For instance, the SecureDrop docroot will
    be under /vagrant in development, but /var/www/securedrop in staging.

    Vars must be stored in `testinfra/vars/<hostname>.yml`.
    """
    filepath = os.path.join(os.path.dirname(__file__), "vars", hostname + ".yml")
    with io.open(filepath, "r") as f:
        hostvars = yaml.safe_load(f)

    hostvars["securedrop_venv_site_packages"] = hostvars["securedrop_venv_site_packages"].format(
        "3.8"
    )  # noqa: E501
    hostvars["python_version"] = "3.8"
    hostvars["apparmor_enforce_actual"] = hostvars["apparmor_enforce"]["focal"]

    # If the tests are run against a production environment, check local config
    # and override as necessary.
    prod_filepath = os.path.join(
        os.path.dirname(__file__), "../../install_files/ansible-base/group_vars/all/site-specific"
    )
    if os.path.isfile(prod_filepath):
        with io.open(prod_filepath, "r") as f:
            prodvars = yaml.safe_load(f)

        def _prod_override(vars_key, prod_key):
            if prod_key in prodvars:
                hostvars[vars_key] = prodvars[prod_key]

        _prod_override("app_ip", "app_ip")
        _prod_override("app_hostname", "app_hostname")
        _prod_override("mon_ip", "monitor_ip")
        _prod_override("monitor_hostname", "monitor_hostname")
        _prod_override("sasl_domain", "sasl_domain")
        _prod_override("sasl_username", "sasl_username")
        _prod_override("sasl_password", "sasl_password")
        _prod_override("daily_reboot_time", "daily_reboot_time")

        # Check repo targeting, and update vars
        repo_filepath = os.path.join(
            os.path.dirname(__file__),
            "../../install_files/ansible-base/roles/install-fpf-repo/defaults/main.yml",
        )  # noqa: E501
        if os.path.isfile(repo_filepath):
            with io.open(repo_filepath, "r") as f:
                repovars = yaml.safe_load(f)
                if "apt_repo_url" in repovars:
                    hostvars["fpf_apt_repo_url"] = repovars["apt_repo_url"]

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
