import pytest


# Hard-coding test vars for development during
# transition from ServerSpec to TestInfra. Test vars
# should be imported based on hostname.
securedrop_test_vars = dict(
    securedrop_user="vagrant",
    securedrop_code="/vagrant/securedrop",
    securedrop_data="/var/lib/securedrop",
)


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


def test_securedrop_application_test_journalist_key(File):
    """
    Ensure the SecureDrop Application GPG public key file is present.
    This is a test-only pubkey provided in the repository strictly for testing.
    """
    pubkey_file = File("{}/test_journalist_key.pub".format(
        securedrop_test_vars['securedrop_data']))
    assert pubkey_file.is_file
    assert pubkey_file.user == "root"
    assert pubkey_file.group == "root"
    assert oct(pubkey_file.mode) == "0644"


    # Let's make sure the corresponding fingerprint is specified
    # in the SecureDrop app configuration.
    securedrop_config = File("{}/config.py".format(
        securedrop_test_vars['securedrop_code']))
    assert securedrop_config.is_file
    assert securedrop_config.user == securedrop_test_vars['securedrop_user']
    assert securedrop_config.group == securedrop_test_vars['securedrop_user']
    assert oct(securedrop_config.mode) == "0600"
    assert securedrop_config.contains(
            "^JOURNALIST_KEY = '65A1B5FF195B56353CC63DFFCC40EF1228271441'$")


def test_securedrop_application_sqlite_db(File):
    """
    Ensure sqlite database exists for application. The database file should be
    created by Ansible on first run.
    """

    f = File("{}/db.sqlite".format(securedrop_test_vars['securedrop_data']))
    assert f.is_file
    assert f.user == securedrop_test_vars['securedrop_user']
    assert f.group == securedrop_test_vars['securedrop_user']
    assert oct(f.mode) == "0644"
