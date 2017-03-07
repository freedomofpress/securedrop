import re
import pytest
from .constants import *

def test_ossec_package(Package):
    """Ensure required packages are installed"""
    for pkg in REQUIRED_OSSEC_SERVER_PACKAGES:
        assert Package(pkg).is_installed

@pytest.mark.parametrize('header', POSTFIX_HEADER_SETTINGS)
def test_postfix_headers(File, header):
    """ Ensure postfix headers contents are kewl """
    f = File(POSTFIX_HEADER_FILE)
    regex = re.escape(header)
    assert f.contains('^{}$'.format(regex))

def test_postfix_headers_attr(File):
    """ Ensure postfix headers file attributes are kewl """
    f = File(POSTFIX_HEADER_FILE)
    assert f.is_file
    assert oct(f.mode) == "0644"

@pytest.mark.parametrize('setting', open(POSTFIX_SETTINGS,'r').readlines())
def test_postfix_settings(File, setting):
    """ Ensure postfix settings contents are right """
    f = File(POSTFIX_SETTINGS_FILE)
    assert f.contains('^{}$'.format(setting))

def test_postfix_settings_attr(File):
    """ Ensure postfix settings file attributes are kewl """
    f = File(POSTFIX_SETTINGS_FILE)
    assert f.is_file
    assert f.user == 'root'
    assert oct(f.mode) == "0644"

def test_ossec_connectivity(Command, Sudo, Ansible):
    """ Ensure ossec considers app-staging host available """
    hostname = Command.check_output("hostname")

    if "staging" in hostname:
        app_hostname = "app-staging"
    app_hostname = "app"
    app_ip = Command.check_output("getent hosts %s | awk '{ print $1 }'" % 
                                  (app_hostname))
    with Sudo():
        list_agents = Command.check_output("/var/ossec/bin/list_agents -a")
        assert list_agents == "%s-%s is available" % (app_hostname, app_ip)

def test_ossec_gnupg(File, Sudo):
    """ ensure ossec gpg homedir exists """
    with Sudo():
        f = File(OSSEC_GNUPG)
        assert f.is_directory
        assert f.user == "ossec"
        assert oct(f.mode) == "0700"

def test_ossec_gnupg(File, Sudo):
    """ ensure ossec gpg homedir exists """
    with Sudo():
        f = File(OSSEC_GNUPG)
        assert f.is_directory
        assert f.user == "ossec"
        assert oct(f.mode) == "0700"

def test_ossec_gnupg(File, Sudo):
    """ ensure test admin gpg pubkey is present """
    with Sudo():
        f = File(OSSEC_ADMIN_KEY)
        assert f.is_file
        assert oct(f.mode) == "0644"

def test_ossec_pubkey_in_keyring(Command, Sudo):
    """ ensure test admin gpg pubkey is in ossec keyring """
    with Sudo("ossec"):
        c = Command("gpg --homedir /var/ossec/.gnupg --list-keys EDDDC102")
        assert OSSEC_GPG_KEY_OUTPUT == c.stdout

@pytest.mark.parametrize('keyfile', OSSEC_KEY_FILES)
def test_ossec_keyfiles(File, Sudo, keyfile):
    with Sudo():
        f = File(keyfile)
        assert f.is_file
        assert oct(f.mode) == "0644"
        assert f.user == "root"

@pytest.mark.parametrize('setting', OSSEC_PROCMAIL_SETTINGS)
def test_procmail_settings(File, Sudo, setting):
    """ Ensure procmail settings contents are right """
    with Sudo():
        f = File(OSSEC_PROCMAIL_FILE)
        assert f.contains('^{}$'.format(setting))

def test_procmail_attrs(File, Sudo):
    """ ensure procmail attributes are correct """
    with Sudo():
        f = File(OSSEC_PROCMAIL_FILE)
        assert f.is_file
        assert f.user == "ossec"
        assert oct(f.mode) == "0644"

def test_procmail_log(File, Sudo):
    """ Ensure procmail log file in place """
    with Sudo():
        f = File(PROCMAIL_LOG)
        assert f.is_file
        assert f.user == "ossec"
        assert oct(f.mode) == "0660"

def test_ossec_authd(Command, Sudo):
    """ Ensure that authd is not running """
    with Sudo():
        c = Command("pgrep ossec-authd")
        assert c.stdout == ""
        assert c.rc != 0

def test_hosts_files(File, Ansible, Command):
    """ Ensure host files mapping are in place """
    f = File('/etc/hosts')

    # If tor isnt running, we are on staging
    if Command("pgrep tor").rc != 0:
        assert f.contains('^127.0.0.1')
        assert f.contains('^127.0.0.1\t*mon-staging\t*mon-staging$')
        assert f.contains('^10.0.1.2\s*app-staging$')
    else:
        # These might be useful later
        #ansible_facts = Ansible("setup")["ansible_facts"]
        #host_vars = Ansible("debug", "msg={{ hostvars }}")['invocation']['module_args']['msg']
        pass

def test_regression_hosts(Command):
    """ Regression test to check for duplicate entries. """
    assert Command.check_output("uniq --repeated /etc/hosts") == ""
