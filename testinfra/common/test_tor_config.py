import pytest
import re

sdvars = pytest.securedrop_test_vars

def test_tor_apt_repo(File):
    """
    Ensure the Tor Project apt repository is configured.
    The version of Tor in the Trusty repos is not up to date.
    """
    f = File('/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list')
    repo_regex = re.escape('deb http://deb.torproject.org/torproject.org trusty main')
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


@pytest.mark.parametrize('torrc_option', [
    'SocksPort 0',
    'SafeLogging 1',
    'RunAsDaemon 1',
    'Sandbox 1',
    'HiddenServiceDir /var/lib/tor/services/ssh',
    'HiddenServicePort 22 127.0.0.1:22',
    'HiddenServiceAuthorizeClient stealth admin',
])
def test_tor_torrc_options(File, torrc_option):
    """
    Check for required options in the system Tor config file.
    These options should be present regardless of machine role,
    meaning both Application and Monitor server will have them.
    """
    f = File("/etc/tor/torrc")
    assert f.is_file
    assert f.user == "debian-tor"
    assert oct(f.mode) == "0644"
    assert f.contains("^{}$".format(torrc_option))


@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_service_directories(File, Sudo, tor_service):
    """
    Check mode and ownership on Tor service directories.
    """
    with Sudo():
        f = File("/var/lib/tor/services/{}".format(tor_service['name']))
        assert f.is_directory
        # TODO: tor might mark these dirs as setgid
        assert oct(f.mode) == "0700"
        assert f.user == "debian-tor"
        assert f.group == "debian-tor"


@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_service_hostnames(File, Sudo, tor_service):
    """
    Check contents of tor service hostname file. For normal Hidden Services,
    the file should contain only hostname (.onion URL). For Authenticated
    Hidden Services, it should also contain the HidServAuth cookie.
    """

    # Declare regex only for THS; we'll build regex for ATHS only if
    # necessary, since we won't have the required values otherwise.
    ths_hostname_regex = "[a-z0-9]{16}\.onion"

    with Sudo():
        f = File("/var/lib/tor/services/{}/hostname".format(tor_service['name']))
        assert f.is_file
        assert oct(f.mode) == "0600"
        assert f.user == "debian-tor"
        assert f.group == "debian-tor"

        # All hostnames should contain at *least* the hostname.
        assert re.search(ths_hostname_regex, f.content)

        if tor_service['authenticated']:
            aths_hostname_regex = ths_hostname_regex+" [a-zA-Z0-9/]{22} # client: "+tor_service['client']
            assert re.search("^{}$".format(aths_hostname_regex), f.content)
        else:
            assert re.search("^{}$".format(ths_hostname_regex), f.content)


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
        tor_status = Command("service tor status")
    assert tor_status.rc == 0
    assert tor_status.stdout == " * tor is running"

    with Sudo():
        tor_enabled = Command("find /etc/rc?.d -name S??tor")
    assert tor_enabled.rc == 0
    assert tor_enabled.stdout != ""

    tor_targets = tor_enabled.stdout.split("\n")
    assert len(tor_targets) == 4
    for target in tor_targets:
        t = File(target)
        assert t.is_symlink
        assert t.linked_to == "/etc/init.d/tor"


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

@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_services_config(File, tor_service):
    """
    Ensure torrc file contains relevant lines for Hidden Service declarations.
    Must include at least `HiddenServiceDir`, and if authenticated, also
    `HiddenServiceAuthorizeClient.
    """
    f = File("/etc/tor/torrc")

    dir_regex = "HiddenServiceDir /var/lib/tor/services/{}".format(
                                                            tor_service['name'])
    assert f.contains("^{}$".format(dir_regex))
    if tor_service['authenticated']:
        auth_regex = "HiddenServiceAuthorizeClient stealth {}".format(
                                                        tor_service['client'])
        assert f.contains("^{}$".format(auth_regex))


@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_dirs(File, Sudo, tor_service):
    """
    Ensure tor service dirs are owned by tor user and mode 0700.
    """
    f = File("/var/lib/tor/services/{}".format(tor_service['name']))
    with Sudo():
        assert f.is_directory
        assert f.user == "debian-tor"
        assert f.group == "debian-tor"
        assert oct(f.mode) == "0700"
