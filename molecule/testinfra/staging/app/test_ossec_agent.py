import os
import re
import pytest

sdvars = pytest.securedrop_test_vars
testinfra_hosts = ["app", "app-staging"]


def test_hosts_files(File, SystemInfo):
    """ Ensure host files mapping are in place """
    f = File('/etc/hosts')

    mon_ip = os.environ.get('MON_IP', sdvars.mon_ip)
    mon_host = sdvars.monitor_hostname

    assert f.contains('^127.0.0.1\s*localhost')
    assert f.contains('^{}\s*{}\s*securedrop-monitor-server-alias$'.format(
                                                                    mon_ip,
                                                                    mon_host))


def test_hosts_duplicate(Command):
    """ Regression test for duplicate entries """
    assert Command.check_output("uniq --repeated /etc/hosts") == ""


def test_ossec_agent_installed(Package):
    """ Check that ossec-agent package is present """
    assert Package("securedrop-ossec-agent").is_installed


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
def test_ossec_keyfile_present(File, Command, Sudo, SystemInfo):
    """ ensure client keyfile for ossec-agent is present """
    pattern = "^1024 {} {} [0-9a-f]{{64}}$".format(
                                    sdvars.app_hostname,
                                    os.environ.get('APP_IP', sdvars.app_ip))
    regex = re.compile(pattern)

    with Sudo():
        f = File("/var/ossec/etc/client.keys")
        assert f.exists
        assert oct(f.mode) == "0644"
        assert f.user == "root"
        assert f.group == "ossec"
        assert f.content_string
        assert bool(re.search(regex, f.content))
