import os
import pytest


testinfra_hosts = ['docker://tor-package-fetcher-xenial']
TOR_DOWNLOAD_DIR = "/tmp/tor-debs"
TOR_PACKAGES = [
    {"name": "tor", "arch": "amd64"},
    {"name": "tor-geoipdb", "arch": "all"},
]
TOR_VERSION = "0.3.5.8-1~xenial+1"


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
    package_name = "{}_{}_{}.deb".format(pkg["name"], TOR_VERSION, pkg["arch"])
    filepath = os.path.join(TOR_DOWNLOAD_DIR, package_name)
    f = host.file(filepath)
    assert f.exists
    assert f.is_file

    cmd = "dpkg-deb -f {} Version".format(filepath)
    package_version = host.check_output(cmd)
    assert package_version == TOR_VERSION


def test_tor_package_platform(host):
    """
    Sanity check to ensure we're running on Xenial, which is the only
    option for SecureDrop distributions supported by upstream Tor Project.
    The Trusty channel was disabled by Tor Project on 2019-01-08.
    """
    assert host.system_info.type == "linux"
    assert host.system_info.distribution == "ubuntu"
    assert host.system_info.codename == "xenial"
    assert host.system_info.release == "16.04"
