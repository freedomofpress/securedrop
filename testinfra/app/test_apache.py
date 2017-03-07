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


# declare required apache packages
@pytest.mark.parametrize("package", [
    "apache2-mpm-worker",
    "libapache2-mod-wsgi",
    "libapache2-mod-xsendfile",
])
def test_apache_apt_packages(Package, package):
    """
    Ensure required Apache packages are installed.
    """
    assert Package(package).is_installed

@pytest.mark.parametrize("apache_opt", [
    "ServerTokens Prod",
    "ServerSignature Off",
    "TraceEnable Off",
])
def test_apache_security_config(File, apache_opt):
    """
    Ensure required apache2 security config file is present.

    Refer to #643, which states that /etc/apache2/security
    is superfluous, and not even used in our config right now.
    We should update the Ansible config to move the file
    to /etc/apache2/conf-available/security.conf.
    """
    f = File("/etc/apache2/security")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"

    assert f.contains("^{}$".format(apache_opt))


# OK to fail here, pending updates to Ansible config.
@pytest.mark.xfail
def test_apache_security_config_deprecated(File):
    """
    Ensure that /etc/apache2/security is absent. See #643 for discussion.
    Tokens set in that file should be moved to
    /etc/apache2/conf-available/security.conf.
    """
    assert not File("/etc/apache2/security").exists
    assert File("/etc/apache2/config-available/security.conf").exists


@pytest.mark.parametrize("apache_opt", [
    'Mutex file:${APACHE_LOCK_DIR} default',
    'PidFile ${APACHE_PID_FILE}',
    'Timeout 60',
    'KeepAlive On',
    'MaxKeepAliveRequests 100',
    'KeepAliveTimeout 5',
    'User www-data',
    'Group www-data',
    'AddDefaultCharset UTF-8',
    'DefaultType None',
    'HostnameLookups Off',
    'ErrorLog /dev/null',
    'LogLevel crit',
    'IncludeOptional mods-enabled/*.load',
    'IncludeOptional mods-enabled/*.conf',
    'Include ports.conf',
    'IncludeOptional sites-enabled/*.conf',
    'ServerTokens Prod',
    'ServerSignature Off',
    'TraceEnable Off',
])
def test_apache_config_settings(File, apache_opt):
    """
    Check required Apache config settings for general server.
    These checks do not target individual interfaces, e.g.
    Source versus Document Interface, and instead apply to
    Apache more generally.
    """
    f = File("/etc/apache2/apache2.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"
    assert re.search("^{}$".format(re.escape(apache_opt)), f.content, re.M)


@pytest.mark.parametrize("port", [
    "80",
    "8080",
])
def test_apache_ports_config(File, SystemInfo, port):
    """
    Ensure Apache ports config items, which specify how the
    Source and Document Interfaces are configured to be served
    over Tor. On staging hosts, they will listen on any interface,
    to permit port forwarding for local testing, but in production,
    they're restricted to localhost, for use over Tor.
    """
    f = File("/etc/apache2/ports.conf")
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"

    listening_regex = "^Listen {}:{}$".format(re.escape(
            securedrop_test_vars['apache_listening_address']), port)
    assert f.contains(listening_regex)


# Setting once so it can be reused in multiple tests.
wanted_apache_headers = [
  'Header edit Set-Cookie ^(.*)$ $1;HttpOnly',
  'Header always append X-Frame-Options: DENY',
  'Header set X-XSS-Protection: "1; mode=block"',
  'Header set X-Content-Type-Options: nosniff',
  'Header set X-Download-Options: noopen',
  'Header set X-Content-Security-Policy: "default-src \'self\'"'
  'Header set Content-Security-Policy: "default-src \'self\'"'
  'Header unset Etag',
]


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
# declare desired apache2 available sites
apache2_available_sites = [
  '/etc/apache2/sites-available/journalist.conf',
  '/etc/apache2/sites-available/source.conf',
]


@pytest.mark.parametrize("apache_opt", [
    'Header set Cache-Control "max-age=1800, must-revalidate"',
    "<VirtualHost {}:80>".format(securedrop_test_vars['apache_listening_address']),
    "DocumentRoot {}/static".format(securedrop_test_vars['securedrop_code']),
    "Alias /static {}/static".format(securedrop_test_vars['securedrop_code']),
    "WSGIDaemonProcess source  processes=2 threads=30 display-name=%{GROUP}"+"python-path={}".format(securedrop_test_vars['securedrop_code']),
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

# declare journalist-specific apache configs
@pytest.mark.parametrize("apache_opt", [
  'Header set Cache-Control "max-age=1800"',
  "<VirtualHost {}:8080>".format(securedrop_test_vars['apache_listening_address']),
  "DocumentRoot {}/static".format(securedrop_test_vars['securedrop_code']),
  "Alias /static {}/static".format(securedrop_test_vars['securedrop_code']),
  "WSGIDaemonProcess journalist  processes=2 threads=30 display-name=%{GROUP}"+" python-path={}".format(securedrop_test_vars['securedrop_code']),
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


# declare apache2 enabled modules
@pytest.mark.parametrize("apache_module", [
  'access_compat',
  'authn_core',
  'alias',
  'authz_core',
  'authz_host',
  'authz_user',
  'deflate',
  'filter',
  'dir',
  'headers',
  'mime',
  'mpm_event',
  'negotiation',
  'reqtimeout',
  'rewrite',
  'wsgi',
  'xsendfile',
])
def test_apache_modules_present(Command, Sudo, apache_module):
    """
    Ensure presence of required Apache modules. Application will not work
    correctly if these are missing. A separate test will check for
    disabled modules.
    """
    with Sudo():
        c = Command("/usr/sbin/a2query -m {}".format(apache_module))
        assert "{} (enabled".format(apache_module) in c.stdout
        assert c.rc == 0


# declare apache2 disabled modules
@pytest.mark.parametrize("apache_module", [
  'auth_basic',
  'authn_file',
  'autoindex',
  'env',
  'setenvif',
  'status',
])
def test_apache_modules_absent(Command, Sudo, apache_module):
    """
    Ensure absence of unwanted Apache modules. Application does not require
    these modules, so they should be disabled to reduce attack surface.
    A separate test will check for disabled modules.
    """
    with Sudo():
        c = Command("/usr/sbin/a2query -m {}".format(apache_module))
        assert "No module matches {} (disabled".format(apache_module) in c.stderr
        assert c.rc == 32


@pytest.mark.parametrize("apache_site", [
    "source",
    "journalist",
])
def test_apache_enabled_sites(Command, Sudo, apache_site):
    """
    Ensure the Source and Journalist interfaces are enabled.
    """
    with Sudo():
        c = Command("/usr/sbin/a2query -s {}".format(apache_site))
        assert "{} (enabled".format(apache_site) in c.stdout
        assert c.rc == 0


@pytest.mark.parametrize("apache_site", [
    "000-default",
])
def test_apache_disabled_sites(Command, apache_site):
    """
    Ensure the default HTML document root is disabled.
    """
    c = Command("a2query -s {}".format(apache_site))
    assert "No site matches {} (disabled".format(apache_site) in c.stdout
    assert c.rc == 32


def test_apache_service(Service):
    """
    Ensure Apache service is running.
    """
    s = Service("apache2")
    assert s.is_running
    assert s.is_enabled


def test_apache_user(User):
    """
    Ensure user account for running application code is configured correctly.
    """
    u = User("www-data")
    assert u.exists
    assert u.home == "/var/www"
    assert u.shell == "/usr/sbin/nologin"

@pytest.mark.parametrize("port", [
    "80"
    "8080",
])
def test_apache_listening(Socket, port):
    """
    Ensure Apache is listening on proper ports and interfaces.
    In staging, expect the service to be bound to 0.0.0.0,
    but in prod, it should be restricted to 127.0.0.1.
    """
    s = Socket("tcp://{}:{}".format(securedrop_test_vars['apache_listening_address'], port))
    assert s.is_listening
