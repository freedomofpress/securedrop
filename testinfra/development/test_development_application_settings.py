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
    assert stderr == "dpkg-query: no packages found matching {}".format(package)


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

  # Vagrant VirtualBox environments show /vagrant as 770,
  # but the Vagrant DigitalOcean droplet shows /vagrant as 775.
  # This appears to be a side-effect of the default umask
  # in the snapci instances. (The rsync provisioner for the
  # vagrant-digitalocean plugin preserves permissions from the host.)
  # The spectests for 'staging' still check for an explicit mode,
  # so it's OK to relax this test for now.
  #it { should be_mode '700' }
  # TODO: should be 700 in all environments; ansible task is
  # straightforward about this.


def test_development_clean_tmp_cron_job(Command, Sudo):
    """
    Ensure cron job for cleaning the temporary directory for the app code exists.
    """

    with Sudo():
        c = Command.check_output('crontab -l')
    # TODO: this should be using property, but the ansible role
    # doesn't use a var, it's hard-coded. update ansible, then fix test.
    # it { should have_entry "@daily #{property['securedrop_code']}/manage.py clean-tmp" }
    assert "@daily {}/manage.py clean-tmp".format(sd_test_vars.securedrop_code) in c


def test_development_default_logo_exists(File):
    """
    Checks for default SecureDrop logo file.

    TODO: Add check for custom logo file.
    """

    f = File("{}/static/i/logo.png".format(sd_test_vars.securedrop_code))
    assert f.is_file
    assert f.user == sd_test_vars.securedrop_user
    assert f.group == sd_test_vars.securedrop_user
    # check if logo is NOT the default securedrop png
    if not f.md5sum == "92443946d5c9e05020a090f97b62d027":
        assert oct(f.mode) == "0400"
