import pytest


securedrop_test_vars = pytest.securedrop_test_vars


@pytest.mark.parametrize("apache_site", [
    "source",
    "journalist",
])
def test_apache_enabled_sites(Command, Sudo, apache_site):
    """
    Ensure the Source and Journalist interfaces are enabled.
    """
    with Sudo():
        c = Command("/usr/sbin/a2query -s {}".format(apache_site))
        assert "{} (enabled".format(apache_site) in c.stdout
        assert c.rc == 0


@pytest.mark.parametrize("apache_site", [
    "000-default",
])
def test_apache_disabled_sites(Command, apache_site):
    """
    Ensure the default HTML document root is disabled.
    """
    c = Command("a2query -s {}".format(apache_site))
    assert "No site matches {} (disabled".format(apache_site) in c.stderr
    assert c.rc == 32


def test_apache_service(Service, Sudo):
    """
    Ensure Apache service is running.
    """
    # Sudo is necessary to run `service apache2 status`, otherwise
    # the service is falsely reported as not running.
    with Sudo():
        s = Service("apache2")
        assert s.is_running
        assert s.is_enabled


def test_apache_user(User):
    """
    Ensure user account for running application code is configured correctly.
    """
    u = User("www-data")
    assert u.exists
    assert u.home == "/var/www"
    assert u.shell == "/usr/sbin/nologin"


@pytest.mark.parametrize("port", [
    "80",
    "8080",
])
def test_apache_listening(Socket, Sudo, port):
    """
    Ensure Apache is listening on proper ports and interfaces.
    In staging, expect the service to be bound to 0.0.0.0,
    but in prod, it should be restricted to 127.0.0.1.
    """
    # Sudo is necessary to read from /proc/net/tcp.
    with Sudo():
        s = Socket("tcp://{}:{}".format(
            securedrop_test_vars.apache_listening_address, port))
        assert s.is_listening
