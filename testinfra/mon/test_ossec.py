import os
import pytest


securedrop_test_vars = pytest.securedrop_test_vars


@pytest.mark.parametrize('package', [
    'mailutils',
    'ossec-server',
    'postfix',
    'procmail',
    'securedrop-ossec-server',
])
def test_ossec_package(Package, package):
    """
    Ensure required packages for OSSEC are installed.
    Includes mail utilities and the FPF-maintained metapackage.
    """
    assert Package(package).is_installed


def test_ossec_connectivity(Command, Sudo):
    """
    Ensure ossec-server machine has active connection to the ossec-agent.
    The ossec service will report all available agents, and we can inspect
    that list to make sure it's the host we expect.
    """
    desired_output = "{}-{} is available.".format(
        securedrop_test_vars.app_hostname,
        os.environ.get('APP_IP', securedrop_test_vars.app_ip))
    with Sudo():
        c = Command.check_output("/var/ossec/bin/list_agents -a")
        assert c == desired_output


def test_ossec_gnupg_homedir(File, Sudo):
    """ ensure ossec gpg homedir exists """
    with Sudo():
        f = File("/var/ossec/.gnupg")
        assert f.is_directory
        assert f.user == "ossec"
        assert oct(f.mode) == "0700"


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
def test_ossec_gnupg(File, Sudo):
    """
    Ensures the test Admin GPG public key is present as file.
    Does not check that it's added to the keyring for the ossec user;
    that's handled by a separate test.
    """
    with Sudo():
        f = File("/var/ossec/test_admin_key.pub")
        assert f.is_file
        assert oct(f.mode) == "0644"


def test_ossec_pubkey_in_keyring(Command, Sudo):
    """
    Ensure the test Admin GPG public key exists in the keyring
    within the ossec home directory.
    """
    ossec_gpg_pubkey_info = """pub   4096R/EDDDC102 2014-10-15
uid                  Test/Development (DO NOT USE IN PRODUCTION) (Admin's OSSEC Alert GPG key) <securedrop@freedom.press>
sub   4096R/97D2EB39 2014-10-15"""  # noqa
    with Sudo("ossec"):
        c = Command.check_output("gpg --homedir /var/ossec/.gnupg "
                                 "--list-keys EDDDC102")
        assert c == ossec_gpg_pubkey_info


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
@pytest.mark.parametrize('keyfile', [
    '/var/ossec/etc/sslmanager.key',
    '/var/ossec/etc/sslmanager.cert',
])
def test_ossec_keyfiles(File, Sudo, keyfile):
    """
    Ensure that the OSSEC transport key pair exists. These keys are used
    to protect the connection between the ossec-server and ossec-agent.

    All this check does in confirm they're present, it doesn't perform any
    matching checks to validate the configuration.
    """
    with Sudo():
        f = File(keyfile)
        assert f.is_file
        # The postinst scripts in the OSSEC deb packages set 440 on the
        # keyfiles; the Ansible config should be updated to do the same.
        assert oct(f.mode) == "0440"
        assert f.user == "root"
        assert f.group == "ossec"


@pytest.mark.parametrize('setting', [
    'VERBOSE=yes',
    'MAILDIR=/var/mail/',
    'DEFAULT=$MAILDIR',
    'LOGFILE=/var/log/procmail.log',
    'SUBJECT=`formail -xSubject:`',
    ':0 c',
    '*^To:.*root.*',
    '|/var/ossec/send_encrypted_alarm.sh',
])
def test_procmail_settings(File, Sudo, setting):
    """
    Ensure procmail settings are correct. These config lines determine
    how the OSSEC email alerts are encrypted and then passed off for sending.
    """
    # Sudo is required to traverse the /var/ossec directory.
    with Sudo():
        f = File("/var/ossec/.procmailrc")
        assert f.contains('^{}$'.format(setting))


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
def test_procmail_attrs(File, Sudo):
    """
    Ensure procmail file attributes are specified correctly.
    """
    with Sudo():
        f = File("/var/ossec/.procmailrc")
        assert f.is_file
        assert f.user == "ossec"
        assert oct(f.mode) == "0440"


# Permissions don't match between Ansible and OSSEC deb packages postinst.
@pytest.mark.xfail
def test_procmail_log(File, Sudo):
    """
    Ensure procmail log file exist with proper ownership.
    Only the ossec user should have read/write permissions.
    """
    with Sudo():
        f = File("/var/log/procmail.log")
        assert f.is_file
        assert f.user == "ossec"
        assert f.group == "root"
        assert oct(f.mode) == "0660"


def test_ossec_authd(Command, Sudo):
    """ Ensure that authd is not running """
    with Sudo():
        c = Command("pgrep ossec-authd")
        assert c.stdout == ""
        assert c.rc != 0


def test_hosts_files(File, SystemInfo):
    """ Ensure host files mapping are in place """
    f = File('/etc/hosts')

    app_ip = os.environ.get('APP_IP', securedrop_test_vars.app_ip)
    app_host = securedrop_test_vars.app_hostname

    assert f.contains('^127.0.0.1.*localhost')
    assert f.contains('^{}\s*{}$'.format(app_ip, app_host))


def test_ossec_log_contains_no_malformed_events(File, Sudo):
    """
    Ensure the OSSEC log reports no errors for incorrectly formatted
    messages. These events indicate that the OSSEC server failed to decrypt
    the event sent by the OSSEC agent, which implies a misconfiguration,
    likely the IPv4 address or keypair differing from what's declared.

    Documentation regarding this error message can be found at:
    http://ossec-docs.readthedocs.io/en/latest/faq/unexpected.html#id4
    """
    with Sudo():
        f = File("/var/ossec/logs/ossec.log")
        assert not f.contains("ERROR: Incorrectly formated message from")


def test_regression_hosts(Command):
    """ Regression test to check for duplicate entries. """
    assert Command.check_output("uniq --repeated /etc/hosts") == ""
