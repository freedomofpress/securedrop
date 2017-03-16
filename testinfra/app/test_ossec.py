import re
import pytest

sdvars = pytest.securedrop_test_vars

def test_hosts_files(File, SystemInfo):
    """ Ensure host files mapping are in place """
    f = File('/etc/hosts')

    hostname = SystemInfo.hostname
    mon_ip = sdvars.mon_ip
    app_host = sdvars.app_hostname
    mon_host = sdvars.monitor_hostname

    assert f.contains('^127.0.0.1')
    assert f.contains('^127.0.0.1\t*{0}\t*{0}$'.format(app_host))
    assert f.contains('^{}\s*{}\s*securedrop-monitor-server-alias$'.format(
                                                                    mon_ip,
                                                                    mon_host))

def test_hosts_duplicate(Command):
    """ Regression test for duplicate entries """
    assert Command.check_output("uniq --repeated /etc/hosts") == ""

def test_ossec_agent_installed(Package):
    """ Check that ossec-agent package is present """
    assert Package("securedrop-ossec-agent").is_installed

def test_ossec_keyfile_present(File, Command, Sudo, SystemInfo):
    """ ensure client keyfile for ossec-agent is present """
    pattern = "^1024 {} {} [0-9a-f]{{64}}$".format(
                                        sdvars.app_hostname,
                                        sdvars.app_ip)
    regex = re.compile(pattern)

    with Sudo():
        f = File("/var/ossec/etc/client.keys")
        assert f.exists
        assert oct(f.mode) == "0644"
        assert f.user == "root"
        assert f.group == "ossec"
        assert f.content_string
        assert bool(re.search(regex, f.content))
