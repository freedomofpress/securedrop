import pytest
import os

hostenv = os.environ['SECUREDROP_TESTINFRA_TARGET_HOST']

sd_test_vars = pytest.securedrop_test_vars


@pytest.mark.parametrize('package', [
    "securedrop-app-code",
    "apache2-mpm-worker",
    "libapache2-mod-wsgi",
    "libapache2-mod-xsendfile",
])
def test_development_lacks_deb_packages(Command, package):
    """
    The development machine does not use Apache, but rather the Flask runner,
    for standing up dev-friendly servers inside the VM. Therefore the
    app-code-related deb packages should be absent.
    """
    # The TestInfra `Package` module doesn't offer state=absent checks,
    # so let's call `dpkg -l` and inspect that output.
    c = Command("dpkg -l {}".format(package))
    assert c.rc == 1
    assert c.stdout == ""
    stderr = c.stderr.rstrip()
    assert stderr == "dpkg-query: no packages found matching {}".format(
        package)


def test_development_apparmor_no_complain_mode(Command, Sudo):
    """
    Ensure that AppArmor profiles are not set to complain mode in development.
    The app-staging host sets profiles to complain, viz.

      * usr.sbin.apache2
      * usr.sbin.tor

    but those changes should not land on the development machine.
    """

    with Sudo():
        c = Command("aa-status")
        if hostenv == "travis":
            assert c.rc == 3
            assert 'apparmor filesystem is not mounted' in c.stderr
        else:
            assert c.rc == 0
            assert '0 profiles are in complain mode.' in c.stdout


@pytest.mark.parametrize('unwanted_file', [
    "/var/www/html",
    "/var/www/source.wsgi",
    "/var/www/document.wsgi",
])
def test_development_apache_docroot_absent(File, unwanted_file):
    """
    Ensure the default HTML document root is missing.
    Development environment does not serve out of /var/www,
    since it uses the Flask dev server, not Apache.
    """
    f = File(unwanted_file)
    assert not f.exists


@pytest.mark.parametrize('data_dir', [
    "/var/lib/securedrop",
    "/var/lib/securedrop/keys",
    "/var/lib/securedrop/tmp",
    "/var/lib/securedrop/store",
])
def test_development_data_directories_exist(File, data_dir):
    """
    Ensure that application code directories are created
    under /vagrant for the development environment, rather than
    /var/www as in staging and prod.
    """
    f = File(data_dir)
    assert f.is_directory
    assert f.user == sd_test_vars.securedrop_user
    assert f.group == sd_test_vars.securedrop_user
    assert oct(f.mode) == "0700"


def test_development_app_directories_exist(File):
    """
    Ensure that application code directories are created
    under /vagrant for the development environment, rather than
    /var/www as in staging and prod.

    Using a separate check from the data directories because /vagrant
    will be mounted with different mode.
    """
    f = File(sd_test_vars.securedrop_code)
    assert f.is_directory
    assert f.user == sd_test_vars.securedrop_user
    assert f.group == sd_test_vars.securedrop_user


def test_development_clean_tmp_cron_job(Command, Sudo):
    """
    Ensure cron job for cleaning the temporary directory for the app code
    exists. Also, ensure that the older format for the cron job is absent,
    since we updated manage.py subcommands to use hyphens instead of
    underscores (e.g. `clean_tmp` -> `clean-tmp`).
    """

    with Sudo():
        c = Command.check_output('crontab -l')
    assert "@daily {}/manage.py clean-tmp".format(
        sd_test_vars.securedrop_code) in c
    assert "@daily {}/manage.py clean_tmp".format(
        sd_test_vars.securedrop_code) not in c
    assert "clean_tmp".format(sd_test_vars.securedrop_code) not in c
    # Make sure that the only cron lines are a comment and the actual job.
    # We don't want any duplicates.
    assert len(c.split("\n")) == 2


def test_development_default_logo_exists(File):
    """
    Checks for default SecureDrop logo file.
    """

    f = File("{}/static/i/logo.png".format(sd_test_vars.securedrop_code))
    assert f.is_file
    assert f.user == sd_test_vars.securedrop_user
    assert f.group == sd_test_vars.securedrop_user
