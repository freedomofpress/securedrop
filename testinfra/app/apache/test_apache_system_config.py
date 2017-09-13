import pytest
import re


securedrop_test_vars = pytest.securedrop_test_vars


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


def test_apache_security_config_deprecated(File):
    """
    Ensure that /etc/apache2/security is absent, since it was setting
    redundant options already presentin /etc/apache2/apache2.conf.
    See #643 for discussion.
    """
    assert not File("/etc/apache2/security").exists


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
            securedrop_test_vars.apache_listening_address), port)
    assert f.contains(listening_regex)


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


@pytest.mark.parametrize("apache_module", [
  'auth_basic',
  'authn_file',
  'autoindex',
  'env',
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
        assert "No module matches {} (disabled".format(apache_module) in \
            c.stderr
        assert c.rc == 32


@pytest.mark.parametrize("logfile",
                         securedrop_test_vars.allowed_apache_logfiles)
def test_apache_logfiles_present(File, Command, Sudo, logfile):
    """"
    Ensure that whitelisted Apache log files for the Source and Journalist
    Interfaces are present. In staging, we permit a "source-error" log,
    but on prod even that is not allowed. A separate test will confirm
    absence of unwanted logfiles by comparing the file count in the
    Apache log directory.
    """
    # We need elevated privileges to read files inside /var/log/apache2
    with Sudo():
        f = File(logfile)
        assert f.is_file
        assert f.user == "root"


def test_apache_logfiles_no_extras(Command, Sudo):
    """
    Ensure that no unwanted Apache logfiles are present. Complements the
    `test_apache_logfiles_present` config test. Here, we confirm that the
    total number of Apache logfiles exactly matches the number permitted
    on the Application Server, whether staging or prod.
    """
    # We need elevated privileges to read files inside /var/log/apache2
    with Sudo():
        c = Command("find /var/log/apache2 -mindepth 1 | wc -l")
        assert int(c.stdout) == \
            len(securedrop_test_vars.allowed_apache_logfiles)
