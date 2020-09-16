import os
import pytest


testinfra_hosts = [
    "docker://tor-package-fetcher-xenial",
    "docker://tor-package-fetcher-focal",
]
TOR_DOWNLOAD_DIR = "/tmp/tor-debs"
TOR_PACKAGES = [
    {"name": "tor", "arch": "amd64"},
    {"name": "tor-geoipdb", "arch": "all"},
]
# The '{}' will be replaced with platform, e.g. Focal
TOR_VERSION_TEMPLATE = "0.4.4.5-1~{}+1"


def test_tor_apt_repo(host):
    """
    Ensure the upstream Tor Project repo is correct, since that's
    where we've fetched the deb packages from.
    """
    repo_file = "/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list"  # noqa
    f = host.file(repo_file)
    assert f.exists
    assert f.contains("https://deb.torproject.org")


@pytest.mark.parametrize("pkg", TOR_PACKAGES)
def test_tor_package_versions(host, pkg):
    """
    Inspect package info and confirm we're getting the version we expect.
    """
    tor_version = TOR_VERSION_TEMPLATE.format(host.system_info.codename)
    package_name = "{}_{}_{}.deb".format(pkg["name"], tor_version, pkg["arch"])
    filepath = os.path.join(TOR_DOWNLOAD_DIR, package_name)
    f = host.file(filepath)
    assert f.exists
    assert f.is_file

    cmd = "dpkg-deb -f {} Version".format(filepath)
    package_version = host.check_output(cmd)
    assert package_version == tor_version


def test_tor_package_platform(host):
    """
    Sanity check to ensure we're running on a version of Ubuntu
    that is supported by the upstream Tor Project, i.e. Xenial or Focal.
    The Trusty channel was disabled by Tor Project on 2019-01-08.
    """
    assert host.system_info.type == "linux"
    assert host.system_info.distribution == "ubuntu"
    assert host.system_info.codename in ("xenial", "focal")
    assert host.system_info.release in ("16.04", "20.04")
