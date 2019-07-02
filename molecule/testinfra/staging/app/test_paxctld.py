import pytest
import re


testinfra_hosts = ["app-staging"]
securedrop_test_vars = pytest.securedrop_test_vars


def test_paxctld_installed(host):
    """
    Ensure the paxctld package is installed.
    """
    # Only relevant to Xenial installs
    if host.system_info.codename == "xenial":
        pkg = host.package("paxctld")
        assert pkg.is_installed


def test_paxctld_config(host):
    """
    Ensure the relevant binaries have appropriate flags set in paxctld config.
    """
    f = host.file("/etc/paxctld.conf")

    # Only relevant to Xenial installs
    if host.system_info.codename == "xenial":
        assert f.is_file
        regex = r"^/usr/sbin/apache2\s+m$"
        assert re.search(regex, f.content_string, re.M)


def test_paxctld_service(host):
    """
    Ensure the paxctld service is enabled and running.
    """
    # Only relevant to Xenial installs
    if host.system_info.codename == "xenial":
        s = host.service("paxctld")
        assert s.is_running
        assert s.is_enabled
