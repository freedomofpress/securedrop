import os.path
import pytest

sdvars = pytest.securedrop_test_vars
testinfra_hosts = [sdvars.app_hostname]


@pytest.mark.parametrize('exp_pip_pkg', sdvars.pip_deps)
def test_app_pip_deps(host, exp_pip_pkg):
    """ Ensure pip dependencies are installed """
    pip = host.pip_package.get_packages(pip_path=os.path.join(sdvars.securedrop_venv_bin, "pip"))
    assert pip[exp_pip_pkg['name']]['version'] == exp_pip_pkg['version']


@pytest.mark.skip_in_prod
def test_app_wsgi(host):
    """ ensure logging is enabled for source interface in staging """
    f = host.file("/var/www/source.wsgi")
    with host.sudo():
        assert f.is_file
        assert f.mode == 0o640
        assert f.user == 'www-data'
        assert f.group == 'www-data'
        assert f.contains("^import logging$")
        assert f.contains(r"^logging\.basicConfig(stream=sys\.stderr)$")


def test_pidfile(host):
    """ ensure there are no pid files """
    assert not host.file('/tmp/journalist.pid').exists
    assert not host.file('/tmp/source.pid').exists


@pytest.mark.parametrize('app_dir', sdvars.app_directories)
def test_app_directories(host, app_dir):
    """ ensure securedrop app directories exist with correct permissions """
    f = host.file(app_dir)
    with host.sudo():
        assert f.is_directory
        assert f.user == sdvars.securedrop_user
        assert f.group == sdvars.securedrop_user
        assert f.mode == 0o700


def test_app_code_pkg(host):
    """ ensure securedrop-app-code package is installed """
    assert host.package("securedrop-app-code").is_installed


def test_app_code_venv(host):
    """
    Ensure the securedrop-app-code virtualenv is correct.
    """
    cmd = """test -z $VIRTUAL_ENV && . {}/bin/activate && test "$VIRTUAL_ENV" = "{}" """.format(
        sdvars.securedrop_venv, sdvars.securedrop_venv
    )

    result = host.run(cmd)
    assert result.rc == 0


def test_supervisor_not_installed(host):
    """ ensure supervisor package is not installed """
    assert host.package("supervisor").is_installed is False


@pytest.mark.skip_in_prod
def test_gpg_key_in_keyring(host):
    """ ensure test gpg key is present in app keyring """
    with host.sudo(sdvars.securedrop_user):
        c = host.run("gpg --homedir /var/lib/securedrop/keys "
                     "--list-keys 28271441")
        assert "pub   4096R/28271441 2013-10-12" in c.stdout


def test_ensure_logo(host):
    """ ensure default logo header file exists """
    f = host.file("{}/static/i/logo.png".format(sdvars.securedrop_code))
    with host.sudo():
        assert f.mode == 0o644
        assert f.user == sdvars.securedrop_user
        assert f.group == sdvars.securedrop_user


def test_securedrop_tmp_clean_cron(host):
    """ Ensure securedrop tmp clean cron job in place """
    with host.sudo():
        cronlist = host.run("crontab -l").stdout
        cronjob = "@daily {}/manage.py clean-tmp".format(sdvars.securedrop_code)
        assert cronjob in cronlist
