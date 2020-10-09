import pytest
import re

import testutils

securedrop_test_vars = testutils.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.app_hostname]


@pytest.mark.parametrize("header", securedrop_test_vars.wanted_apache_headers)
def test_apache_headers_source_interface(host, header):
    """
    Test for expected headers in Source Interface vhost config.
    """
    f = host.file("/etc/apache2/sites-available/source.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
    header_regex = "^{}$".format(re.escape(header))
    assert re.search(header_regex, f.content_string, re.M)


@pytest.mark.parametrize("apache_opt", [
    "<VirtualHost {}:80>".format(
        securedrop_test_vars.apache_listening_address),
    "WSGIDaemonProcess source  processes=2 threads=30 display-name=%{{GROUP}} python-path={}".format(  # noqa
        securedrop_test_vars.securedrop_code),
    'WSGIProcessGroup source',
    'WSGIScriptAlias / /var/www/source.wsgi',
    'Header set Cache-Control "no-store"',
    'Header set Referrer-Policy "same-origin"',
    "Alias /static {}/static".format(securedrop_test_vars.securedrop_code),
    """
<Directory {}/static>
  Order allow,deny
  Allow from all
  # Cache static resources for 1 hour
  Header set Cache-Control "max-age=3600"
</Directory>
""".strip('\n').format(securedrop_test_vars.securedrop_code),
    'XSendFile        Off',
    'LimitRequestBody 524288000',
    'ErrorDocument 400 /notfound',
    'ErrorDocument 401 /notfound',
    'ErrorDocument 403 /notfound',
    'ErrorDocument 404 /notfound',
    'ErrorDocument 500 /notfound',
    "ErrorLog {}".format(securedrop_test_vars.apache_source_log),
])
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
