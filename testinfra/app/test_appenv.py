import pytest

sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('exp_pip_pkg', sdvars.pip_deps)
def test_app_pip_deps(PipPackage, exp_pip_pkg):
    """ Ensure pip dependencies are installed """
    pip = PipPackage.get_packages()
    assert pip[exp_pip_pkg['name']]['version'] == exp_pip_pkg['version']


def test_app_wsgi(File, Sudo):
    """ ensure logging is enabled for source interface in staging """
    f = File("/var/www/source.wsgi")
    with Sudo():
        assert f.is_file
        assert oct(f.mode) == "0640"
        assert f.user == 'www-data'
        assert f.group == 'www-data'
        assert f.contains("^import logging$")
        assert f.contains("^logging\.basicConfig(stream=sys\.stderr)$")


def test_pidfile(File):
    """ ensure there are no pid files """
    assert not File('/tmp/journalist.pid').exists
    assert not File('/tmp/source.pid').exists


@pytest.mark.parametrize('app_dir', sdvars.app_directories)
def test_app_directories(File, Sudo, app_dir):
    """ ensure securedrop app directories exist with correct permissions """
    f = File(app_dir)
    with Sudo():
        assert f.is_directory
        assert f.user == sdvars.securedrop_user
        assert f.group == sdvars.securedrop_user
        assert oct(f.mode) == "0700"


def test_app_code_pkg(Package):
    """ ensure securedrop-app-code package is installed """
    assert Package("securedrop-app-code").is_installed


def test_gpg_key_in_keyring(Command, Sudo):
    """ ensure test gpg key is present in app keyring """
    with Sudo(sdvars.securedrop_user):
        c = Command("gpg --homedir /var/lib/securedrop/keys "
                    "--list-keys 28271441")
        assert "pub   4096R/28271441 2013-10-12" in c.stdout


def test_ensure_logo(File, Sudo):
    """ ensure default logo header file exists """
    f = File("{}/static/i/logo.png".format(sdvars.securedrop_code))
    with Sudo():
        assert oct(f.mode) == "0644"
        assert f.user == sdvars.securedrop_user
        assert f.group == sdvars.securedrop_user


def test_securedrop_tmp_clean_cron(Command, Sudo):
    """ Ensure securedrop tmp clean cron job in place """
    with Sudo():
        cronlist = Command("crontab -l").stdout
        cronjob = "@daily {}/manage.py clean-tmp".format(
            sdvars.securedrop_code)
        assert cronjob in cronlist


def test_app_workerlog_dir(File, Sudo):
    """ ensure directory for worker logs is present """
    f = File('/var/log/securedrop_worker')
    with Sudo():
        assert f.is_directory
        assert f.user == "root"
        assert f.group == "root"
        assert oct(f.mode) == "0644"
