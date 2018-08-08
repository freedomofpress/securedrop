import pytest
import re


testinfra_hosts = ["app-staging"]
sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_service_directories(File, Sudo, tor_service):
    """
    Check mode and ownership on Tor service directories.
    """
    with Sudo():
        f = File("/var/lib/tor/services/{}".format(tor_service['name']))
        assert f.is_directory
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
        f = File("/var/lib/tor/services/{}/hostname".format(
            tor_service['name']))
        assert f.is_file
        assert oct(f.mode) == "0600"
        assert f.user == "debian-tor"
        assert f.group == "debian-tor"

        # All hostnames should contain at *least* the hostname.
        assert re.search(ths_hostname_regex, f.content)

        if tor_service['authenticated']:
            # HidServAuth regex is approximately [a-zA-Z0-9/+], but validating
            # the entire entry is sane, and we don't need to nitpick the
            # charset.
            aths_hostname_regex = ths_hostname_regex + " .{22} # client: " + \
                                  tor_service['client']
            assert re.search("^{}$".format(aths_hostname_regex), f.content)
        else:
            assert re.search("^{}$".format(ths_hostname_regex), f.content)


@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_services_config(File, tor_service):
    """
    Ensure torrc file contains relevant lines for Hidden Service declarations.
    All hidden services must include:

      * HiddenServiceDir
      * HiddenServicePort

    Only authenticated hidden services must also include:

      * HiddenServiceAuthorizeClient

    Check for each as appropriate.
    """
    f = File("/etc/tor/torrc")
    dir_regex = "HiddenServiceDir /var/lib/tor/services/{}".format(
        tor_service['name'])
    # We need at least one port, but it may be used for both config values.
    # On the Journalist Interface, we reuse the "80" remote port but map it to
    # a different local port, so Apache can listen on several sockets.
    remote_port = tor_service['ports'][0]
    try:
        local_port = tor_service['ports'][1]
    except IndexError:
        local_port = remote_port

    port_regex = "HiddenServicePort {} 127.0.0.1:{}".format(
            remote_port, local_port)

    assert f.contains("^{}$".format(dir_regex))
    assert f.contains("^{}$".format(port_regex))

    if tor_service['authenticated']:
        auth_regex = "HiddenServiceAuthorizeClient stealth {}".format(
                tor_service['client'])
        assert f.contains("^{}$".format(auth_regex))
