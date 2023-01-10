import pytest
import testutils

securedrop_test_vars = testutils.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.app_hostname]


@pytest.mark.parametrize(
    "apache_site",
    [
        "source",
        "journalist",
    ],
)
def test_apache_enabled_sites(host, apache_site):
    """
    Ensure the Source and Journalist interfaces are enabled.
    """
    with host.sudo():
        c = host.run(f"/usr/sbin/a2query -s {apache_site}")
        assert f"{apache_site} (enabled" in c.stdout
        assert c.rc == 0


@pytest.mark.parametrize(
    "apache_site",
    [
        "000-default",
    ],
)
def test_apache_disabled_sites(host, apache_site):
    """
    Ensure the default HTML document root is disabled.
    """
    c = host.run(f"a2query -s {apache_site}")
    assert f"No site matches {apache_site} (disabled" in c.stderr
    assert c.rc == 32


def test_apache_service(host):
    """
    Ensure Apache service is running.
    """
    # sudo is necessary to run `service apache2 status`, otherwise
    # the service is falsely reported as not running.
    with host.sudo():
        s = host.service("apache2")
        assert s.is_running
        assert s.is_enabled


def test_apache_user(host):
    """
    Ensure user account for running application code is configured correctly.
    """
    u = host.user("www-data")
    assert u.exists
    assert u.home == "/var/www"
    assert u.shell == "/usr/sbin/nologin"


@pytest.mark.parametrize(
    "port",
    [
        "80",
        "8080",
    ],
)
def test_apache_listening(host, port):
    """
    Ensure Apache is listening on proper ports and interfaces.
    In staging, expect the service to be bound to 0.0.0.0,
    but in prod, it should be restricted to 127.0.0.1.
    """
    # sudo is necessary to read from /proc/net/tcp.
    with host.sudo():
        s = host.socket(f"tcp://{securedrop_test_vars.apache_listening_address}:{port}")
        assert s.is_listening
