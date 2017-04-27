import re
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


@pytest.mark.parametrize('header', [
    '/^X-Originating-IP:/    IGNORE',
    '/^X-Mailer:/    IGNORE',
    '/^Mime-Version:/        IGNORE',
    '/^User-Agent:/  IGNORE',
    '/^Received:/    IGNORE',
])
def test_postfix_headers(File, header):
    """
    Ensure postfix header filters are set correctly. Common mail headers
    are stripped by default to avoid leaking metadata about the instance.
    Message body is always encrypted prior to sending.
    """
    f = File("/etc/postfix/header_checks")
    assert f.is_file
    assert oct(f.mode) == "0644"
    regex = '^{}$'.format(re.escape(header))
    assert re.search(regex, f.content, re.M)


@pytest.mark.parametrize('setting', [
    'relayhost = [smtp.gmail.com]:587',
    'smtp_sasl_auth_enable = yes',
    'smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd',
    'smtp_sasl_security_options = noanonymous',
    'smtp_use_tls = yes',
    'smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache',
    'smtp_tls_security_level = secure',
    'smtp_tls_CApath = /etc/ssl/certs',
    'smtp_tls_ciphers = high',
    'smtp_tls_protocols = TLSv1.2 TLSv1.1 TLSv1 !SSLv3 !SSLv2',
    'myhostname = ossec.server',
    'myorigin = $myhostname',
    'smtpd_banner = $myhostname ESMTP $mail_name (Ubuntu)',
    'biff = no',
    'append_dot_mydomain = no',
    'readme_directory = no',
    'smtp_header_checks = regexp:/etc/postfix/header_checks',
    'mailbox_command = /usr/bin/procmail',
    'inet_interfaces = loopback-only',
    'alias_maps = hash:/etc/aliases',
    'alias_database = hash:/etc/aliases',
    'mydestination = $myhostname, localhost.localdomain , localhost',
    'mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128',
    'mailbox_size_limit = 0',
    'recipient_delimiter = +',
])
def test_postfix_settings(File, setting):
    """
    Check all postfix configuration lines. There are technically multiple
    configuration paths regarding the TLS settings, particularly the
    fingerprint verification logic, but only the base default config is tested
    currently.
    """
    f = File("/etc/postfix/main.cf")
    assert f.is_file
    assert f.user == 'root'
    assert oct(f.mode) == "0644"
    regex = '^{}$'.format(re.escape(setting))
    assert re.search(regex, f.content, re.M)


def test_ossec_connectivity(Command, Sudo):
    """
    Ensure ossec-server machine has active connection to the ossec-agent.
    The ossec service will report all available agents, and we can inspect
    that list to make sure it's the host we expect.
    """
    desired_output = "{}-{} is available.".format(securedrop_test_vars.app_hostname,
            securedrop_test_vars.app_ip)
    with Sudo():
        c = Command.check_output("/var/ossec/bin/list_agents -a")
        assert c == desired_output

def test_ossec_gnupg(File, Sudo):
    """ ensure ossec gpg homedir exists """
    with Sudo():
        f = File(OSSEC_GNUPG)
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
sub   4096R/97D2EB39 2014-10-15"""
    with Sudo("ossec"):
        c = Command.check_output("gpg --homedir /var/ossec/.gnupg --list-keys EDDDC102")
        assert c ==  ossec_gpg_pubkey_info


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
        # The postinst scripts in the OSSEC deb packages set 440 on the keyfiles;
        # the Ansible config should be updated to do the same.
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

# Currently failing in CI under remote hosts
# Looks like vagrant is currently appending hostname to local IP
@pytest.mark.xfail
def test_hosts_files(File, SystemInfo):
    """ Ensure host localhost is mapping to servername """
    f = File('/etc/hosts')
    mon_host = securedrop_test_vars.monitor_hostname
    assert f.contains('^127.0.0.1.*{0}$'.format(mon_host))

def test_hosts_files(File, SystemInfo):
    """ Ensure host files mapping are in place """
    f = File('/etc/hosts')

    hostname = SystemInfo.hostname
    app_ip = securedrop_test_vars.app_ip
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


def test_postfix_generic_maps(File):
    """
    Regression test to check that generic Postfix maps are not configured
    by default. As of #1565 Admins can opt-in to overriding the FROM address
    used for sending OSSEC alerts, but by default we're preserving the old
    `ossec@ossec.server` behavior, to avoid breaking email for previously
    existing instances.
    """
    assert not File("/etc/postfix/generic").exists
    assert not File("/etc/postfix/main.cf").contains("^smtp_generic_maps")
