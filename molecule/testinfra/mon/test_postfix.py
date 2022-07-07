import re

import pytest
import testutils

securedrop_test_vars = testutils.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.monitor_hostname]


@pytest.mark.parametrize(
    "header",
    [
        "/^X-Originating-IP:/    IGNORE",
        "/^X-Mailer:/    IGNORE",
        "/^Mime-Version:/        IGNORE",
        "/^User-Agent:/  IGNORE",
        "/^Received:/    IGNORE",
    ],
)
def test_postfix_headers(host, header):
    """
    Ensure postfix header filters are set correctly. Common mail headers
    are stripped by default to avoid leaking metadata about the instance.
    Message body is always encrypted prior to sending.
    """
    f = host.file("/etc/postfix/header_checks")
    assert f.is_file
    assert f.mode == 0o644
    regex = "^{}$".format(re.escape(header))
    assert re.search(regex, f.content_string, re.M)


def test_postfix_generic_maps(host):
    """
    Check configuration of Postfix generic map when sasl_domain is set
    and ossec_from_address is not specified.
    """
    assert host.file("/etc/postfix/generic").exists
    assert host.file("/etc/postfix/generic").contains(
        "^ossec@{} {}@{}".format(
            securedrop_test_vars.monitor_hostname,
            securedrop_test_vars.sasl_username,
            securedrop_test_vars.sasl_domain,
        )
    )
    assert host.file("/etc/postfix/main.cf").contains("^smtp_generic_maps")
    assert host.file("/etc/postfix/main.cf").contains(
        "^smtpd_recipient_restrictions = reject_unauth_destination"
    )


def test_postfix_service(host):
    """
    Check Postfix service. Postfix is used to deliver OSSEC alerts via
    encrypted email. On staging hosts, Postfix is disabled, due to lack
    of SASL authentication credentials, but on prod hosts it should run.
    """
    # Elevated privileges are required to read Postfix service info,
    # specifically `/var/spool/postfix/pid/master.pid`.
    with host.sudo():
        postfix = host.service("postfix")
        assert postfix.is_running == securedrop_test_vars.postfix_enabled
        assert postfix.is_enabled == securedrop_test_vars.postfix_enabled

        socket = host.socket("tcp://127.0.0.1:25")
        assert socket.is_listening == securedrop_test_vars.postfix_enabled
