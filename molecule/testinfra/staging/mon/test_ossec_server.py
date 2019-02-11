import os
import pytest


testinfra_hosts = ["mon-staging"]
securedrop_test_vars = pytest.securedrop_test_vars


def test_ossec_connectivity(host):
    """
    Ensure ossec-server machine has active connection to the ossec-agent.
    The ossec service will report all available agents, and we can inspect
    that list to make sure it's the host we expect.
    """
    desired_output = "{}-{} is available.".format(
        securedrop_test_vars.app_hostname,
        os.environ.get('APP_IP', securedrop_test_vars.app_ip))
    with host.sudo():
        c = host.check_output("/var/ossec/bin/list_agents -a")
        assert c == desired_output


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
@pytest.mark.parametrize('keyfile', [
    '/var/ossec/etc/sslmanager.key',
    '/var/ossec/etc/sslmanager.cert',
])
def test_ossec_keyfiles(host, keyfile):
    """
    Ensure that the OSSEC transport key pair exists. These keys are used
    to protect the connection between the ossec-server and ossec-agent.

    All this check does in confirm they're present, it doesn't perform any
    matching checks to validate the configuration.
    """
    with host.sudo():
        f = host.file(keyfile)
        assert f.is_file
        # The postinst scripts in the OSSEC deb packages set 440 on the
        # keyfiles; the Ansible config should be updated to do the same.
        assert oct(f.mode) == "0440"
        assert f.user == "root"
        assert f.group == "ossec"


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
def test_procmail_log(host):
    """
    Ensure procmail log file exist with proper ownership.
    Only the ossec user should have read/write permissions.
    """
    with host.sudo():
        f = host.file("/var/log/procmail.log")
        assert f.is_file
        assert f.user == "ossec"
        assert f.group == "root"
        assert oct(f.mode) == "0660"


def test_ossec_authd(host):
    """ Ensure that authd is not running """
    with host.sudo():
        c = host.run("pgrep ossec-authd")
        assert c.stdout == ""
        assert c.rc != 0


def test_hosts_files(host):
    """ Ensure host files mapping are in place """
    f = host.file('/etc/hosts')

    app_ip = os.environ.get('APP_IP', securedrop_test_vars.app_ip)
    app_host = securedrop_test_vars.app_hostname

    assert f.contains('^127.0.0.1.*localhost')
    assert f.contains('^{}\s*{}$'.format(app_ip, app_host))


def test_ossec_log_contains_no_malformed_events(host):
    """
    Ensure the OSSEC log reports no errors for incorrectly formatted
    messages. These events indicate that the OSSEC server failed to decrypt
    the event sent by the OSSEC agent, which implies a misconfiguration,
    likely the IPv4 address or keypair differing from what's declared.

    Documentation regarding this error message can be found at:
    http://ossec-docs.readthedocs.io/en/latest/faq/unexpected.html#id4
    """
    with host.sudo():
        f = host.file("/var/ossec/logs/ossec.log")
        assert not f.contains("ERROR: Incorrectly formated message from")


def test_regression_hosts(host):
    """ Regression test to check for duplicate entries. """
    assert host.check_output("uniq --repeated /etc/hosts") == ""
