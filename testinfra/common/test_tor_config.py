import pytest
import re

sdvars = pytest.securedrop_test_vars


def test_tor_apt_repo(File):
    """
    Ensure the Tor Project apt repository is configured.
    The version of Tor in the Trusty repos is not up to date.
    """
    f = File('/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list')
    repo_regex = re.escape('deb http://tor-apt.ops.freedom.press trusty main')
    assert f.contains(repo_regex)


@pytest.mark.parametrize('package', [
    'deb.torproject.org-keyring',
    'tor',
])
def test_tor_packages(Package, package):
    """
    Ensure Tor packages are installed. Includes a check for the keyring,
    so that automatic updates can handle rotating the signing key if necessary.
    """
    assert Package(package).is_installed


def test_tor_service_running(Command, File, Sudo):
    """
    Ensure tor is running and enabled. Tor is required for SSH access,
    so it must be enabled to start on boot.
    """
    # TestInfra tries determine the service manager intelligently, and
    # inappropriately assumes Upstart on Trusty, due to presence of the
    # `initctl` command. The tor service is handled via a SysV-style init
    # script, so let's just shell out and verify the running and enabled
    # states explicitly.
    with Sudo():
        assert Command.check_output("service tor status") == \
               " * tor is running"
        tor_enabled = Command.check_output("find /etc/rc?.d -name S??tor")

    assert tor_enabled != ""

    tor_targets = tor_enabled.split("\n")
    assert len(tor_targets) == 4
    for target in tor_targets:
        t = File(target)
        assert t.is_symlink
        assert t.linked_to == "/etc/init.d/tor"


@pytest.mark.parametrize('torrc_option', [
    'SocksPort 0',
    'SafeLogging 1',
    'RunAsDaemon 1',
])
def test_tor_torrc_options(File, torrc_option):
    """
    Check for required options in the system Tor config file.
    These options should be present regardless of machine role,
    meaning both Application and Monitor server will have them.

    Separate tests will check for specific hidden services.
    """
    f = File("/etc/tor/torrc")
    assert f.is_file
    assert f.user == "debian-tor"
    assert oct(f.mode) == "0644"
    assert f.contains("^{}$".format(torrc_option))


def test_tor_torrc_sandbox(File):
    """
    Check that the `Sandbox 1` declaration is not present in the torrc.
    The torrc manpage states this option is experimental, and although we
    use it already on Tails workstations, further testing is required
    before we push it out to servers. See issues #944 and #1969.
    """
    f = File("/etc/tor/torrc")
    # Only `Sandbox 1` will enable, but make sure there are zero occurrances
    # of "Sandbox", otherwise we may have a regression somewhere.
    assert not f.contains("^.*Sandbox.*$")


def test_tor_signing_key_fingerprint(Command):
    """
    The `deb.torproject.org-keyring` package manages the repo signing pubkey
    for tor-related packages, so make sure that fingerprint matches
    expectations.
    """

    c = Command("apt-key finger")
    tor_gpg_pub_key_info = """/etc/apt/trusted.gpg.d/deb.torproject.org-keyring.gpg
-----------------------------------------------------
pub   2048R/886DDD89 2009-09-04 [expires: 2020-08-29]
      Key fingerprint = A3C4 F0F9 79CA A22C DBA8  F512 EE8C BC9E 886D DD89
uid                  deb.torproject.org archive signing key
sub   2048R/219EC810 2009-09-04 [expires: 2018-08-30]"""

    assert c.rc == 0
    assert tor_gpg_pub_key_info in c.stdout
