import pytest
import re


test_vars = pytest.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


@pytest.mark.parametrize('dependency', [
    'cron-apt',
    'ntp'
])
def test_cron_apt_dependencies(host, dependency):
    """
    Ensure critical packages are installed. If any of these are missing,
    the system will fail to receive automatic updates.

    The current apt config uses cron-apt, rather than unattended-upgrades,
    but this may change in the future. Previously the apt.freedom.press repo
    was not reporting any "Origin" field, making use of unattended-upgrades
    problematic. With better procedures in place regarding apt repo
    maintenance, we can ensure the field is populated going forward.
    """
    assert host.package(dependency).is_installed


def test_cron_apt_config(host):
    """
    Ensure custom cron-apt config file is present.
    """
    f = host.file('/etc/cron-apt/config')
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    assert f.contains('^SYSLOGON="always"$')
    assert f.contains('^EXITON=error$')


@pytest.mark.parametrize('repo', [
  'deb http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security main',
  'deb-src http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security main',
  'deb http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security universe',
  'deb-src http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security universe',
  'deb [arch=amd64] {fpf_apt_repo_url} {securedrop_target_platform} main',
])
def test_cron_apt_repo_list(host, repo):
    """
    Ensure the correct apt repositories are specified
    in the security list for apt.
    """
    repo_config = repo.format(
        fpf_apt_repo_url=test_vars.fpf_apt_repo_url,
        securedrop_target_platform=host.system_info.codename
    )
    f = host.file('/etc/apt/security.list')
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    repo_regex = '^{}$'.format(re.escape(repo_config))
    assert f.contains(repo_regex)


def test_cron_apt_repo_config_update(host):
    """
    Ensure cron-apt updates repos from the security.list config.
    """

    f = host.file('/etc/cron-apt/action.d/0-update')
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    repo_config = str('update -o quiet=2'
                      ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                      ' -o Dir::Etc::SourceParts=""')
    assert f.contains('^{}$'.format(repo_config))


def test_cron_apt_delete_vanilla_kernels(host):
    """
    Ensure cron-apt removes generic linux image packages when installed.
    """

    f = host.file('/etc/cron-apt/action.d/9-remove')
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    command = str('remove -y'
                  ' linux-image-generic-lts-xenial linux-image-.*generic'
                  ' -o quiet=2')
    assert f.contains('^{}$'.format(command))


def test_cron_apt_repo_config_upgrade(host):
    """
    Ensure cron-apt upgrades packages from the security.list config.
    """
    f = host.file('/etc/cron-apt/action.d/5-security')
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    assert f.contains('^autoclean -y$')
    repo_config = str('dist-upgrade -y -o APT::Get::Show-Upgraded=true'
                      ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                      ' -o Dpkg::Options::=--force-confdef'
                      ' -o Dpkg::Options::=--force-confold')
    assert f.contains(re.escape(repo_config))


def test_cron_apt_config_deprecated(host):
    """
    Ensure default cron-apt file to download all updates does not exist.
    """
    f = host.file('/etc/cron-apt/action.d/3-download')
    assert not f.exists


@pytest.mark.parametrize('cron_job', [
    {'job': '0 4 * * * root    /usr/bin/test -x /usr/sbin/cron-apt && /usr/sbin/cron-apt && /sbin/reboot', # noqa
     'state': 'present'},
    {'job': '0 4 * * * root    /usr/bin/test -x /usr/sbin/cron-apt && /usr/sbin/cron-apt', # noqa
     'state': 'absent'},
    {'job': '0 5 * * * root    /sbin/reboot',
     'state': 'absent'},
])
def test_cron_apt_cron_jobs(host, cron_job):
    """
    Check for correct cron job for upgrading all packages and rebooting.
    We'll also check for absence of previous versions of the cron job,
    to make sure those have been cleaned up via the playbooks.
    """
    f = host.file('/etc/cron.d/cron-apt')
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644

    regex_job = '^{}$'.format(re.escape(cron_job['job']))
    if cron_job['state'] == 'present':
        assert f.contains(regex_job)
    else:
        assert not f.contains(regex_job)


def test_cron_apt_all_packages_updated(host):
    """
    Ensure a safe-upgrade has already been run, by checking that no
    packages are eligible for upgrade currently.

    The Ansible config installs a specific, out-of-date version of Firefox
    for use with Selenium. Therefore apt will report it's possible to upgrade
    Firefox, which we'll need to mark as "OK" in terms of the tests.
    """
    c = host.run('aptitude --simulate -y safe-upgrade')
    assert c.rc == 0
    # Staging hosts will have locally built deb packages, marked as held.
    # Staging and development will have a version-locked Firefox pinned for
    # Selenium compatibility; if the holds are working, they shouldn't be
    # upgraded.
    assert "No packages will be installed, upgraded, or removed." in c.stdout
