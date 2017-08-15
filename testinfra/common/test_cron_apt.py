import pytest
import re


@pytest.mark.parametrize('dependency', [
    'cron-apt',
    'ntp'
])
def test_cron_apt_dependencies(Package, dependency):
    """
    Ensure critical packages are installed. If any of these are missing,
    the system will fail to receive automatic updates.

    The current apt config uses cron-apt, rather than unattended-upgrades,
    but this may change in the future. Previously the apt.freedom.press repo
    was not reporting any "Origin" field, making use of unattended-upgrades
    problematic. With better procedures in place regarding apt repo
    maintenance, we can ensure the field is populated going forward.
    """
    assert Package(dependency).is_installed


def test_cron_apt_config(File):
    """
    Ensure custom cron-apt config file is present.
    """
    f = File('/etc/cron-apt/config')
    assert f.is_file
    assert f.user == "root"
    assert oct(f.mode) == "0644"
    assert f.contains('^SYSLOGON="always"$')
    assert f.contains('^EXITON=error$')


@pytest.mark.parametrize('repo', [
  'deb http://security.ubuntu.com/ubuntu trusty-security main',
  'deb-src http://security.ubuntu.com/ubuntu trusty-security main',
  'deb http://security.ubuntu.com/ubuntu trusty-security universe',
  'deb-src http://security.ubuntu.com/ubuntu trusty-security universe',
  'deb [arch=amd64] https://apt.freedom.press trusty main',
  'deb http://tor-apt.ops.freedom.press trusty main',
])
def test_cron_apt_repo_list(File, repo):
    """
    Ensure the correct apt repositories are specified
    in the security list for apt.
    """
    f = File('/etc/apt/security.list')
    assert f.is_file
    assert f.user == "root"
    assert oct(f.mode) == "0644"
    repo_regex = '^{}$'.format(re.escape(repo))
    assert f.contains(repo_regex)


def test_cron_apt_repo_config_update(File):
    """
    Ensure cron-apt updates repos from the security.list config.
    """

    f = File('/etc/cron-apt/action.d/0-update')
    assert f.is_file
    assert f.user == "root"
    assert oct(f.mode) == "0644"
    repo_config = str('update -o quiet=2'
                      ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                      ' -o Dir::Etc::SourceParts=""')
    assert f.contains('^{}$'.format(repo_config))


def test_cron_apt_repo_config_upgrade(File):
    """
    Ensure cron-apt upgrades packages from the security.list config.
    """
    f = File('/etc/cron-apt/action.d/5-security')
    assert f.is_file
    assert f.user == "root"
    assert oct(f.mode) == "0644"
    assert f.contains('^autoclean -y$')
    repo_config = str('dist-upgrade -y -o APT::Get::Show-Upgraded=true'
                      ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                      ' -o Dpkg::Options::=--force-confdef'
                      ' -o Dpkg::Options::=--force-confold')
    assert f.contains(re.escape(repo_config))


def test_cron_apt_config_deprecated(File):
    """
    Ensure default cron-apt file to download all updates does not exist.
    """
    f = File('/etc/cron-apt/action.d/3-download')
    assert not f.exists


@pytest.mark.parametrize('cron_job', [
    {'job': '0 4 * * * root    /usr/bin/test -x /usr/sbin/cron-apt && /usr/sbin/cron-apt && /sbin/reboot', # noqa
     'state': 'present'},
    {'job': '0 4 * * * root    /usr/bin/test -x /usr/sbin/cron-apt && /usr/sbin/cron-apt', # noqa
     'state': 'absent'},
    {'job': '0 5 * * * root    /sbin/reboot',
     'state': 'absent'},
])
def test_cron_apt_cron_jobs(File, cron_job):
    """
    Check for correct cron job for upgrading all packages and rebooting.
    We'll also check for absence of previous versions of the cron job,
    to make sure those have been cleaned up via the playbooks.
    """
    f = File('/etc/cron.d/cron-apt')
    assert f.is_file
    assert f.user == "root"
    assert oct(f.mode) == "0644"

    regex_job = '^{}$'.format(re.escape(cron_job['job']))
    if cron_job['state'] == 'present':
        assert f.contains(regex_job)
    else:
        assert not f.contains(regex_job)


def test_cron_apt_all_packages_updated(Command):
    """
    Ensure a safe-upgrade has already been run, by checking that no
    packages are eligible for upgrade currently.

    The Ansible config installs a specific, out-of-date version of Firefox
    for use with Selenium. Therefore apt will report it's possible to upgrade
    Firefox, which we'll need to mark as "OK" in terms of the tests.
    """
    c = Command('aptitude --simulate -y safe-upgrade')
    assert c.rc == 0
    # Staging hosts will have locally built deb packages, marked as held.
    # Staging and development will have a version-locked Firefox pinned for
    # Selenium compatibility; if the holds are working, they shouldn't be
    # upgraded.
    assert "No packages will be installed, upgraded, or removed." in c.stdout
