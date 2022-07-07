import re

import pytest
import testutils

securedrop_test_vars = testutils.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.app_hostname]


@pytest.mark.parametrize("header, value", securedrop_test_vars.wanted_apache_headers.items())
def test_apache_headers_source_interface(host, header, value):
    """
    Test for expected headers in Source Interface vhost config.
    """
    f = host.file("/etc/apache2/sites-available/source.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
    header_unset = "Header onsuccess unset {}".format(header)
    assert f.contains(header_unset)
    header_set = 'Header always set {} "{}"'.format(header, value)
    assert f.contains(header_set)


@pytest.mark.parametrize(
    "apache_opt",
    [
        "<VirtualHost {}:80>".format(securedrop_test_vars.apache_listening_address),
        "WSGIDaemonProcess source  processes=2 threads=30 display-name=%{{GROUP}} python-path={}".format(  # noqa
            securedrop_test_vars.securedrop_code
        ),
        "WSGIProcessGroup source",
        "WSGIScriptAlias / /var/www/source.wsgi",
        'Header set Cache-Control "no-store"',
        "Header unset Etag",
        "Alias /static {}/static".format(securedrop_test_vars.securedrop_code),
        "XSendFile        Off",
        "LimitRequestBody 524288000",
        "ErrorLog {}".format(securedrop_test_vars.apache_source_log),
    ],
)
def test_apache_config_source_interface(host, apache_opt):
    """
    Ensure the necessary Apache settings for serving the application
    are in place. Some values will change according to the host,
    e.g. app-staging versus app-prod will have different listening
    addresses, depending on whether Tor connections are forced.

    These checks apply only to the Source Interface, used by Sources.
    """
    f = host.file("/etc/apache2/sites-available/source.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
    regex = "^{}$".format(re.escape(apache_opt))
    assert re.search(regex, f.content_string, re.M)


def test_apache_config_source_interface_headers_per_distro(host):
    """
    During migration to Focal, we updated the syntax for forcing HTTP headers.
    """
    f = host.file("/etc/apache2/sites-available/source.conf")
    assert f.contains("Header onsuccess unset X-Frame-Options")
    assert f.contains('Header always set X-Frame-Options "DENY"')
    assert f.contains("Header onsuccess unset Referrer-Policy")
    assert f.contains('Header always set Referrer-Policy "same-origin"')
    assert f.contains("Header edit Set-Cookie ^(.*)$ $1;HttpOnly")


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
  <Limit GET POST HEAD>
    Require ip 127.0.0.1
  </Limit>
  <LimitExcept GET POST HEAD>
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
def test_apache_config_source_interface_access_control(host, apache_opt):
    """
    Verifies the access control directives for the Source Interface.
    """
    f = host.file("/etc/apache2/sites-available/source.conf")
    regex = "^{}$".format(re.escape(apache_opt))
    assert re.search(regex, f.content_string, re.M)
