import pytest

testinfra_hosts = ["app-staging"]
sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('package', [
    'tor',
])
def test_tor_packages(Package, package):
    """
    Ensure Tor packages are installed. Does not include the Tor keyring
    package, since we want only the SecureDrop Release Signing Key
    to be used even for Tor packages.
    """
    assert Package(package).is_installed


def test_tor_service_running(host):
    """
    Ensure tor is running and enabled. Tor is required for SSH access,
    so it must be enabled to start on boot. Checks systemd-style services,
    used by Xenial.
    """
    s = host.service("tor")
    assert s.is_running
    assert s.is_enabled


@pytest.mark.parametrize('torrc_option', [
    'SocksPort 0',
    'SafeLogging 1',
    'RunAsDaemon 1',
])
def test_tor_torrc_options(host, torrc_option):
    """
    Check for required options in the system Tor config file.
    These options should be present regardless of machine role,
    meaning both Application and Monitor server will have them.

    Separate tests will check for specific hidden services.
    """
    f = host.file("/etc/tor/torrc")
    assert f.is_file
    assert f.user == "debian-tor"
    assert oct(f.mode) == "0644"
    assert f.contains("^{}$".format(torrc_option))


def test_tor_torrc_sandbox(host):
    """
    Check that the `Sandbox 1` declaration is not present in the torrc.
    The torrc manpage states this option is experimental, and although we
    use it already on Tails workstations, further testing is required
    before we push it out to servers. See issues #944 and #1969.
    """
    f = host.file("/etc/tor/torrc")
    # Only `Sandbox 1` will enable, but make sure there are zero occurrances
    # of "Sandbox", otherwise we may have a regression somewhere.
    assert not f.contains("^.*Sandbox.*$")
