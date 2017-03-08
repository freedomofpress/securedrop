import pytest

sdvars = pytest.securedrop_test_vars

@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_settings(File, tor_service):
    """ ensure torrc for contains appropriate services """
    f = File("/etc/tor/torrc")
    assert f.contains("HiddenServiceDir /var/lib/tor/services/{}".format(
                                                                tor_service))

@pytest.mark.parametrize('tor_service', sdvars.tor_stealth_services)
def test_tor_hidden_service_cfg(Command, tor_service):
    c = Command("awk '/{}/{{getline; print}}' /etc/tor/torrc".format(
                                                        tor_service['service']))
    assert c.stdout == "HiddenServiceAuthorizeClient stealth {}".format(
                                                        tor_service['stealth'])

@pytest.mark.parametrize('tor_service', sdvars.tor_services)
def test_tor_dirs(File, Sudo, tor_service):
    """ ensure tor service dirs are owned by tor user and mode 0700 """
    f = File("/var/lib/tor/services/{}".format(tor_service))
    with Sudo():
        assert f.is_directory
        assert f.user == "debian-tor"
        assert f.group == "debian-tor"
        assert oct(f.mode) == "0700"
