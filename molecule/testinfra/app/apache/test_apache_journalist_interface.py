import re

import pytest
import testutils

securedrop_test_vars = testutils.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.app_hostname]


@pytest.mark.parametrize("header, value", securedrop_test_vars.wanted_apache_headers.items())
def test_apache_headers_journalist_interface(host, header, value):
    """
    Test for expected headers in Document Interface vhost config.
    """
    f = host.file("/etc/apache2/sites-available/journalist.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
    header_unset = "Header onsuccess unset {}".format(header)
    assert f.contains(header_unset)
    header_set = 'Header always set {} "{}"'.format(header, value)
    assert f.contains(header_set)


# declare journalist-specific Apache configs
@pytest.mark.parametrize(
    "apache_opt",
    [
        "<VirtualHost {}:8080>".format(securedrop_test_vars.apache_listening_address),
        "WSGIDaemonProcess journalist processes=2 threads=30 display-name=%{{GROUP}} python-path={}".format(  # noqa
            securedrop_test_vars.securedrop_code
        ),
        (
            "WSGIScriptAlias / /var/www/journalist.wsgi "
            "process-group=journalist application-group=journalist"
        ),
        "WSGIPassAuthorization On",
        'Header set Cache-Control "no-store"',
        "Alias /static {}/static".format(securedrop_test_vars.securedrop_code),
        "XSendFile        On",
        "LimitRequestBody 524288000",
        "XSendFilePath    /var/lib/securedrop/store/",
        "XSendFilePath    /var/lib/securedrop/tmp/",
        "ErrorLog /var/log/apache2/journalist-error.log",
        "CustomLog /var/log/apache2/journalist-access.log combined",
    ],
)
def test_apache_config_journalist_interface(host, apache_opt):
    """
    Ensure the necessary Apache settings for serving the application
    are in place. Some values will change according to the host,
    e.g. app-staging versus app-prod will have different listening
    addresses, depending on whether Tor connections are forced.

    These checks apply only to the Document Interface, used by Journalists.
    """
    f = host.file("/etc/apache2/sites-available/journalist.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
    regex = "^{}$".format(re.escape(apache_opt))
    assert re.search(regex, f.content_string, re.M)


def test_apache_config_journalist_interface_headers_per_distro(host):
    """
    During migration to Focal, we updated the syntax for forcing HTTP headers.
    """
    f = host.file("/etc/apache2/sites-available/journalist.conf")
    assert f.contains("Header onsuccess unset X-Frame-Options")
    assert f.contains('Header always set X-Frame-Options "DENY"')
    assert f.contains("Header onsuccess unset Referrer-Policy")
    assert f.contains('Header always set Referrer-Policy "no-referrer"')
    assert f.contains("Header edit Set-Cookie ^(.*)$ $1;HttpOnly")


def test_apache_logging_journalist_interface(host):
    """
    Check that logging is configured correctly for the Journalist Interface.
    The actions of Journalists are logged by the system, so that an Admin can
    investigate incidents and track access.

    Logs were broken for some period of time, logging only "combined" to
    the logfile, rather than the combined LogFormat intended.
    """
    # sudo is necessary because /var/log/apache2 is mode 0750.
    with host.sudo():
        f = host.file("/var/log/apache2/journalist-access.log")
        assert f.is_file
        if f.size == 0:
            # If the file is empty, the Journalist Interface hasn't been used
            # yet, so make a quick GET request local to the host so we can
            # validate the log entry.
            host.check_output("curl http://127.0.0.1:8080")

        assert f.size > 0  # Make sure something was logged.
        # LogFormat declaration was missing, so track regressions that log
        # just the string "combined" and nothing else.
        assert not f.contains("^combined$")
        assert f.contains("GET")


@pytest.mark.parametrize(
    "apache_opt",
    [
        """
<Directory />
  Options None
  AllowOverride None
  Require all denied
</Directory>
""".strip(
            "\n"
        ),
        """
<Directory {}/static>
  Require all granted
  # Cache static resources for 1 hour
  Header set Cache-Control "max-age=3600"
</Directory>
""".strip(
            "\n"
        ).format(
            securedrop_test_vars.securedrop_code
        ),
        """
<Directory {}>
  Options None
  AllowOverride None
  <Limit GET POST HEAD DELETE>
    Require ip 127.0.0.1
  </Limit>
  <LimitExcept GET POST HEAD DELETE>
    Require all denied
  </LimitExcept>
</Directory>
""".strip(
            "\n"
        ).format(
            securedrop_test_vars.securedrop_code
        ),
    ],
)
def test_apache_config_journalist_interface_access_control(host, apache_opt):
    """
    Verifies the access control directives for the Journalist Interface.
    """
    f = host.file("/etc/apache2/sites-available/journalist.conf")
    regex = "^{}$".format(re.escape(apache_opt))
    assert re.search(regex, f.content_string, re.M)
