import re
import pytest


securedrop_test_vars = pytest.securedrop_test_vars


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


def test_postfix_service(Service, Socket, Sudo):
    """
    Check Postfix service. Postfix is used to deliver OSSEC alerts via
    encrypted email. On staging hosts, Postfix is disabled, due to lack
    of SASL authentication credentials, but on prod hosts it should run.
    """
    # Elevated privileges are required to read Postfix service info,
    # specifically `/var/spool/postfix/pid/master.pid`.
    with Sudo():
        postfix = Service("postfix")
        assert postfix.is_running == securedrop_test_vars.postfix_enabled
        assert postfix.is_enabled == securedrop_test_vars.postfix_enabled

        socket = Socket("tcp://127.0.0.1:25")
        assert socket.is_listening == securedrop_test_vars.postfix_enabled
