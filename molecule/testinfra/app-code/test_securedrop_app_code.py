import pytest


securedrop_test_vars = pytest.securedrop_test_vars
testinfra_hosts = [securedrop_test_vars.app_hostname]


def test_apache_default_docroot_is_absent(host):
    """
    Ensure that the default docroot for Apache, containing static HTML
    under Debian, has been removed. Leaving it in place can be a privacy
    leak, as it displays version information by default.
    """
    assert not host.file('/var/www/html').exists


@pytest.mark.parametrize('package', [
    'apache2',
    'apparmor-utils',
    'coreutils',
    'gnupg2',
    'haveged',
    'libapache2-mod-xsendfile',
    'libpython3.5',
    'paxctld',
    'python3',
    'redis-server',
    'securedrop-config',
    'securedrop-keyring',
    'sqlite3',
])
def test_securedrop_application_apt_dependencies(host, package):
    """
    Ensure apt dependencies required to install `securedrop-app-code`
    are present. These should be pulled in automatically via apt,
    due to specification in Depends in package control file.
    """
    assert host.package(package).is_installed


@pytest.mark.skip_in_prod
def test_securedrop_application_test_locale(host):
    """
    Ensure both SecureDrop DEFAULT_LOCALE and SUPPORTED_LOCALES are present.
    """
    securedrop_config = host.file("{}/config.py".format(
        securedrop_test_vars.securedrop_code))
    with host.sudo():
        assert securedrop_config.is_file
        assert securedrop_config.contains("^DEFAULT_LOCALE")
        assert securedrop_config.content_string.count("DEFAULT_LOCALE") == 1
        assert securedrop_config.content_string.count("SUPPORTED_LOCALES") == 1
        assert "\nSUPPORTED_LOCALES = ['el', 'ar', 'en_US']\n" in securedrop_config.content_string


@pytest.mark.skip_in_prod
def test_securedrop_application_test_journalist_key(host):
    """
    Ensure the SecureDrop Application GPG public key file is present.
    This is a test-only pubkey provided in the repository strictly for testing.
    """
    pubkey_file = host.file("{}/test_journalist_key.pub".format(
        securedrop_test_vars.securedrop_data))
    # sudo is only necessary when testing against app hosts, since the
    # permissions are tighter. Let's elevate privileges so we're sure
    # we can read the correct file attributes and test them.
    with host.sudo():
        assert pubkey_file.is_file
        assert pubkey_file.user == "root"
        assert pubkey_file.group == "root"
        assert pubkey_file.mode == 0o644

    # Let's make sure the corresponding fingerprint is specified
    # in the SecureDrop app configuration.
    securedrop_config = host.file("{}/config.py".format(
        securedrop_test_vars.securedrop_code))
    with host.sudo():
        assert securedrop_config.is_file
        assert securedrop_config.user == \
            securedrop_test_vars.securedrop_user
        assert securedrop_config.group == \
            securedrop_test_vars.securedrop_user
        assert securedrop_config.mode == 0o600
        assert securedrop_config.contains(
            "^JOURNALIST_KEY = '65A1B5FF195B56353CC63DFFCC40EF1228271441'$")


def test_securedrop_application_sqlite_db(host):
    """
    Ensure sqlite database exists for application. The database file should be
    created by Ansible on first run.
    """
    # sudo is necessary under the App hosts, which have restrictive file
    # permissions on the doc root. Not technically necessary under dev host.
    with host.sudo():
        f = host.file("{}/db.sqlite".format(securedrop_test_vars.securedrop_data))
        assert f.is_file
        assert f.user == securedrop_test_vars.securedrop_user
        assert f.group == securedrop_test_vars.securedrop_user
        assert f.mode == 0o640
