import pytest
import re


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

# Test is not DRY; haven't figured out how to parametrize on
# multiple inputs, so explicitly redeclaring test logic.
@pytest.mark.parametrize("header", wanted_apache_headers)
def test_apache_headers_journalist_interface(File, header):
    """
    Test for expected headers in Document Interface vhost config.
    """
    f = File("/etc/apache2/sites-available/journalist.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"
    header_regex = "^{}$".format(re.escape(header))
    assert re.search(header_regex, f.content, re.M)

# declare block of directory declarations common to both
# source and journalist interfaces.
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
    allow from #{property['apache_allow_from']}
  </Limit>
  <LimitExcept GET POST HEAD>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>

<Directory #{property['securedrop_code']}>
  Options None
  AllowOverride None
  <Limit GET POST HEAD>
    Order allow,deny
    allow from #{property['apache_allow_from']}
  </Limit>
  <LimitExcept GET POST HEAD>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>
""".lstrip().rstrip()


# declare journalist-specific apache configs
@pytest.mark.parametrize("apache_opt", [
  'Header set Cache-Control "max-age=1800"',
  "<VirtualHost {}:8080>".format(securedrop_test_vars['apache_listening_address']),
  "DocumentRoot {}/static".format(securedrop_test_vars['securedrop_code']),
  "Alias /static {}/static".format(securedrop_test_vars['securedrop_code']),
  "WSGIDaemonProcess journalist processes=2 threads=30 display-name=%{GROUP}"+" python-path={}".format(securedrop_test_vars['securedrop_code']),
  'WSGIProcessGroup journalist',
  'WSGIScriptAlias / /var/www/journalist.wsgi/',
  'AddType text/html .py',
  'XSendFile        On',
  'XSendFilePath    /var/lib/securedrop/store/',
  'XSendFilePath    /var/lib/securedrop/tmp/',
  'ErrorLog /var/log/apache2/journalist-error.log',
  'CustomLog /var/log/apache2/journalist-access.log combined',
])
def test_apache_config_journalist_interface(File, apache_opt):
    """
    Ensure the necessary Apache settings for serving the application
    are in place. Some values will change according to the host,
    e.g. app-staging versus app-prod will have different listening
    addresses, depending on whether Tor connections are forced.

    These checks apply only to the Document Interface, used by Journalists.
    """
    f = File("/etc/apache2/sites-available/journalist.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"
    regex = "^{}$".format(re.escape(apache_opt))
    assert re.search(regex, f.content, re.M)


# Expect to fail pending fix for LogFormat declaration.
@pytest.mark.xfail
def test_apache_logging_journalist_interface(File):
    """
    Check that logging is configured correctly for the Journalist Interface.
    The actions of Journalists are logged by the system, so that an Admin can
    investigate incidents and track access.

    Logs were broken for some period of time, logging only "combined" to the logfile,
    rather than the combined LogFormat intended.
    """
    f = File("/var/log/apache2/journalist-access.log")
    assert f.is_file
    assert f.size > 0 # will fail if no journalist account used
    assert not f.contains("^combined$")
