import pytest
import re


testinfra_hosts = ["app-staging"]
securedrop_test_vars = pytest.securedrop_test_vars

# Setting once so it can be reused in multiple tests.
wanted_apache_headers = [
  'Header edit Set-Cookie ^(.*)$ $1;HttpOnly',
  'Header always append X-Frame-Options: DENY',
  'Header set Referrer-Policy "no-referrer"',
  'Header set X-XSS-Protection: "1; mode=block"',
  'Header set X-Content-Type-Options: nosniff',
  'Header set X-Download-Options: noopen',
  "Header set X-Content-Security-Policy: \"default-src 'self'\"",
  "Header set Content-Security-Policy: \"default-src 'self'\"",
  'Header set Referrer-Policy "no-referrer"',
]


# Test is not DRY; haven't figured out how to parametrize on
# multiple inputs, so explicitly redeclaring test logic.
@pytest.mark.parametrize("header", wanted_apache_headers)
def test_apache_headers_journalist_interface(host, header):
    """
    Test for expected headers in Document Interface vhost config.
    """
    f = host.file("/etc/apache2/sites-available/journalist.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
    header_regex = "^{}$".format(re.escape(header))
    assert re.search(header_regex, f.content_string, re.M)


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
  <Limit GET POST HEAD DELETE>
    Order allow,deny
    allow from {apache_allow_from}
  </Limit>
  <LimitExcept GET POST HEAD DELETE>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>

<Directory {securedrop_code}>
  Options None
  AllowOverride None
  <Limit GET POST HEAD DELETE>
    Order allow,deny
    allow from {apache_allow_from}
  </Limit>
  <LimitExcept GET POST HEAD DELETE>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>
""".lstrip().rstrip().format(
        apache_allow_from=securedrop_test_vars.apache_allow_from,
        securedrop_code=securedrop_test_vars.securedrop_code)


# declare journalist-specific apache configs
@pytest.mark.parametrize("apache_opt", [
  "<VirtualHost {}:8080>".format(
      securedrop_test_vars.apache_listening_address),
  "WSGIDaemonProcess journalist processes=2 threads=30 display-name=%{{GROUP}} python-path={}".format(  # noqa
      securedrop_test_vars.securedrop_code),
  'WSGIProcessGroup journalist',
  'WSGIScriptAlias / /var/www/journalist.wsgi',
  'WSGIPassAuthorization On',
  'Header set Cache-Control "no-store"',
  "Alias /static {}/static".format(securedrop_test_vars.securedrop_code),
  """
<Directory {}/static>
  Order allow,deny
  Allow from all
  # Cache static resources for 1 hour
  Header set Cache-Control "max-age=3600"
</Directory>
""".strip('\n').format(securedrop_test_vars.securedrop_code),
  'XSendFile        On',
  'LimitRequestBody 524288000',
  'XSendFilePath    /var/lib/securedrop/store/',
  'XSendFilePath    /var/lib/securedrop/tmp/',
  'ErrorLog /var/log/apache2/journalist-error.log',
  'CustomLog /var/log/apache2/journalist-access.log combined',
])
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


def test_apache_journalist_interface_vhost(host):
    """
    Ensure the document root is configured with correct access restrictions
    for serving Journalist Interface application code.
    """
    f = host.file("/etc/apache2/sites-available/journalist.conf")
    assert common_apache2_directory_declarations in f.content_string


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
