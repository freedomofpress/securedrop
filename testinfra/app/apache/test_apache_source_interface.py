import pytest
import re


# Setting once so it can be reused in multiple tests.
wanted_apache_headers = [
  'Header edit Set-Cookie ^(.*)$ $1;HttpOnly',
  'Header always append X-Frame-Options: DENY',
  'Header set X-XSS-Protection: "1; mode=block"',
  'Header set X-Content-Type-Options: nosniff',
  'Header set X-Download-Options: noopen',
  "Header set X-Content-Security-Policy: \"default-src 'self'\"",
  "Header set Content-Security-Policy: \"default-src 'self'\"",
  'Header unset Etag',
]
# Hard-coding test vars for development during
# transition from ServerSpec to TestInfra. Test vars
# should be imported based on hostname.
securedrop_test_vars = dict(
    securedrop_user="vagrant",
    securedrop_code="/var/www/securedrop",
    securedrop_data="/var/lib/securedrop",
    apache_allow_from="all",
    apache_listening_address="0.0.0.0",
    apache_source_log="/var/log/apache2/source-error.log",
)


@pytest.mark.parametrize("header", wanted_apache_headers)
def test_apache_headers_source_interface(File, header):
    """
    Test for expected headers in Source Interface vhost config.
    """
    f = File("/etc/apache2/sites-available/source.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"
    header_regex = "^{}$".format(re.escape(header))
    assert re.search(header_regex, f.content, re.M)


@pytest.mark.parametrize("apache_opt", [
    'Header set Cache-Control "max-age=1800, must-revalidate"',
    "<VirtualHost {}:80>".format(securedrop_test_vars['apache_listening_address']),
    "DocumentRoot {}/static".format(securedrop_test_vars['securedrop_code']),
    "Alias /static {}/static".format(securedrop_test_vars['securedrop_code']),
    "WSGIDaemonProcess source  processes=2 threads=30 display-name=%{GROUP}"+" python-path={}".format(securedrop_test_vars['securedrop_code']),
    'WSGIProcessGroup source',
    'WSGIScriptAlias / /var/www/source.wsgi/',
    'AddType text/html .py',
    'XSendFile        Off',
    'LimitRequestBody 524288000',
    'ErrorDocument 400 /notfound',
    'ErrorDocument 401 /notfound',
    'ErrorDocument 403 /notfound',
    'ErrorDocument 404 /notfound',
    'ErrorDocument 500 /notfound',
    "ErrorLog {}".format(securedrop_test_vars['apache_source_log']),
])
def test_apache_config_source_interface(File, apache_opt):
    """
    Ensure the necessary Apache settings for serving the application
    are in place. Some values will change according to the host,
    e.g. app-staging versus app-prod will have different listening
    addresses, depending on whether Tor connections are forced.

    These checks apply only to the Source Interface, used by Sources.
    """
    f = File("/etc/apache2/sites-available/source.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"
    regex = "^{}$".format(re.escape(apache_opt))
    assert re.search(regex, f.content, re.M)

# Block of directory declarations for Apache vhost is common
# to both Source and Journalist interfaces. Hardcoding these values
# across multiple test files to speed up development; they should be
# written once and imported in a DRY manner.
common_apache2_directory_declarations = """
<Directory />
  Options None
  AllowOverride None
  Order deny,allow
  Deny from all
</Directory>

<Directory /var/www/>
  Options None
  AllowOverride None
  <Limit GET POST HEAD>
    Order allow,deny
    allow from {apache_allow_from}
  </Limit>
  <LimitExcept GET POST HEAD>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>

<Directory {securedrop_code}>
  Options None
  AllowOverride None
  <Limit GET POST HEAD>
    Order allow,deny
    allow from {apache_allow_from}
  </Limit>
  <LimitExcept GET POST HEAD>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>
""".lstrip().rstrip().format(**securedrop_test_vars)


def test_apache_source_interface_vhost(File):
    """
    Ensure the document root is configured with correct access restrictions
    for serving Source Interface application code.
    """
    f = File("/etc/apache2/sites-available/source.conf")
    assert common_apache2_directory_declarations in f.content


def test_apache_logging_source_interface(File, Sudo, SystemInfo):
    """
    Check that Source Interface logging is enabled in staging,
    but disabled in prod.
    """
    # Sudo is required to traverse /var/log/apache2.
    with Sudo():
        f = File("/var/log/apache2/source-error.log")
        # Logfile should not exist on prod, but should on staging.
        if SystemInfo.hostname.endswith('-prod'):
            assert not f.exists
        else:
            assert f.exists
