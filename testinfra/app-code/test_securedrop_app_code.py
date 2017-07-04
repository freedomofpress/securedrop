import os
import pytest


securedrop_test_vars = pytest.securedrop_test_vars
hostenv = os.environ['SECUREDROP_TESTINFRA_TARGET_HOST']


def test_apache_default_docroot_is_absent(File):
    """
    Ensure that the default docroot for Apache, containing static HTML
    under Debian, has been removed. Leaving it in place can be a privacy
    leak, as it displays version information by default.
    """
    assert not File('/var/www/html').exists


@pytest.mark.parametrize('package', [
  'apparmor-utils',
  'gnupg2',
  'haveged',
  'python',
  'python-pip',
  'redis-server',
  'secure-delete',
  'sqlite',
  'supervisor',
])
def test_securedrop_application_apt_dependencies(Package, package):
    """
    Ensure apt dependencies required to install `securedrop-app-code`
    are present. These should be pulled in automatically via apt,
    due to specification in Depends in package control file.
    """
    assert Package(package).is_installed


def test_securedrop_application_test_locale(File, Sudo):
    """
    Ensure SecureDrop DEFAULT_LOCALE is present.
    """
    securedrop_config = File("{}/config.py".format(
        securedrop_test_vars.securedrop_code))
    with Sudo():
        assert securedrop_config.is_file
        assert securedrop_config.contains("^DEFAULT_LOCALE")
        assert securedrop_config.content.count("DEFAULT_LOCALE") == 1


def test_securedrop_application_test_journalist_key(File, Sudo):
    """
    Ensure the SecureDrop Application GPG public key file is present.
    This is a test-only pubkey provided in the repository strictly for testing.
    """
    pubkey_file = File("{}/test_journalist_key.pub".format(
        securedrop_test_vars.securedrop_data))
    # Sudo is only necessary when testing against app hosts, since the
    # permissions are tighter. Let's elevate privileges so we're sure
    # we can read the correct file attributes and test them.
    with Sudo():
        assert pubkey_file.is_file
        assert pubkey_file.user == "root"
        assert pubkey_file.group == "root"
        assert oct(pubkey_file.mode) == "0644"

    # Let's make sure the corresponding fingerprint is specified
    # in the SecureDrop app configuration.
    securedrop_config = File("{}/config.py".format(
        securedrop_test_vars.securedrop_code))
    with Sudo():
        assert securedrop_config.is_file
        # travis needs the config.py file ran owned by root not sure why
        # just saw this note in the travis.yml config
        if hostenv == "travis":
            assert securedrop_config.user == "root"
            assert securedrop_config.group == "root"
        else:
            assert securedrop_config.user == \
                securedrop_test_vars.securedrop_user
            assert securedrop_config.group == \
                securedrop_test_vars.securedrop_user
        assert oct(securedrop_config.mode) == "0600"
        assert securedrop_config.contains(
            "^JOURNALIST_KEY = '65A1B5FF195B56353CC63DFFCC40EF1228271441'$")


def test_securedrop_application_sqlite_db(File, Sudo):
    """
    Ensure sqlite database exists for application. The database file should be
    created by Ansible on first run.
    """
    # Sudo is necessary under the App hosts, which have restrictive file
    # permissions on the doc root. Not technically necessary under dev host.
    with Sudo():
        f = File("{}/db.sqlite".format(securedrop_test_vars.securedrop_data))
        assert f.is_file
        assert f.user == securedrop_test_vars.securedrop_user
        assert f.group == securedrop_test_vars.securedrop_user
        assert oct(f.mode) == "0644"
