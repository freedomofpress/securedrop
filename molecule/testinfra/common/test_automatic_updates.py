import pytest
import re

import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_automatic_updates_dependencies(host):
    """
    Ensure critical packages are installed. If any of these are missing,
    the system will fail to receive automatic updates.

    In Xenial, the apt config uses cron-apt, rather than unattended-upgrades.
    Previously the apt.freedom.press repo was not reporting any "Origin" field,
    making use of unattended-upgrades problematic.
    In Focal, the apt config uses unattended-upgrades.
    """
    apt_dependencies = {
        'xenial': ['cron-apt', 'ntp'],
        'focal': ['unattended-upgrades', 'ntp']
    }

    for package in apt_dependencies[host.system_info.codename]:
        assert host.package(package).is_installed


def test_cron_apt_config(host):
    """
    Ensure custom cron-apt config file is present in Xenial, and absent in Focal
    """
    f = host.file('/etc/cron-apt/config')
    if host.system_info.codename == "xenial":
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        assert f.contains('^SYSLOGON="always"$')
        assert f.contains('^EXITON=error$')
    else:
        assert not f.exists


@pytest.mark.parametrize('repo', [
  'deb http://security.ubuntu.com/ubuntu {securedrop_target_distribution}-security main',
  'deb-src http://security.ubuntu.com/ubuntu {securedrop_target_distribution}-security main',
  'deb http://security.ubuntu.com/ubuntu {securedrop_target_distribution}-security universe',
  'deb-src http://security.ubuntu.com/ubuntu {securedrop_target_distribution}-security universe',
  'deb [arch=amd64] {fpf_apt_repo_url} {securedrop_target_distribution} main',
])
def test_cron_apt_repo_list(host, repo):
    """
    Ensure the correct apt repositories are specified
    in the security list for apt.
    """
    repo_config = repo.format(
        fpf_apt_repo_url=test_vars.fpf_apt_repo_url,
        securedrop_target_distribution=host.system_info.codename
    )
    f = host.file('/etc/apt/security.list')
    if host.system_info.codename == "xenial":
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        repo_regex = '^{}$'.format(re.escape(repo_config))
        assert f.contains(repo_regex)
    else:
        assert not f.exists


@pytest.mark.parametrize('repo', [
  'deb http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security main',
  'deb http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security universe',
  'deb http://archive.ubuntu.com/ubuntu/ {securedrop_target_platform}-updates main',
  'deb http://archive.ubuntu.com/ubuntu/ {securedrop_target_platform} main'
])
def test_sources_list(host, repo):
    """
    Ensure the correct apt repositories are specified
    in the sources.list for apt.
    """
    repo_config = repo.format(
        securedrop_target_platform=host.system_info.codename
    )
    f = host.file('/etc/apt/sources.list')
    if host.system_info.codename == "focal":
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        repo_regex = '^{}$'.format(re.escape(repo_config))
        assert f.contains(repo_regex)


def test_cron_apt_repo_config_update(host):
    """
    Ensure cron-apt updates repos from the security.list config for Xenial.
    """

    f = host.file('/etc/cron-apt/action.d/0-update')
    if host.system_info.codename == "xenial":
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        repo_config = str('update -o quiet=2'
                          ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                          ' -o Dir::Etc::SourceParts=""')
        assert f.contains('^{}$'.format(repo_config))
    else:
        assert not f.exists


def test_cron_apt_delete_vanilla_kernels(host):
    """
    Ensure cron-apt removes generic linux image packages when installed. This
    file is provisioned via ansible and via the securedrop-config package. We
    should remove it once Xenial is fully deprecated. In the meantime, it will
    not impact Focal systems running unattended-upgrades
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
    if host.system_info.codename == "xenial":
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        assert f.contains('^autoclean -y$')
        repo_config = str('dist-upgrade -y -o APT::Get::Show-Upgraded=true'
                          ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                          ' -o Dpkg::Options::=--force-confdef'
                          ' -o Dpkg::Options::=--force-confold')
        assert f.contains(re.escape(repo_config))
    else:
        assert not f.exists


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

    if host.system_info.codename == "xenial":
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644

        regex_job = '^{}$'.format(re.escape(cron_job['job']))
        if cron_job['state'] == 'present':
            assert f.contains(regex_job)
        else:
            assert not f.contains(regex_job)
    else:
        assert not f.exists


def test_unattended_upgrades_config(host):
    """
    Ensures the 50unattended-upgrades config is correct only under Ubuntu Focal
    """
    f = host.file('/etc/apt/apt.conf.d/50unattended-upgrades')
    if host.system_info.codename == "xenial":
        assert not f.exists
    else:
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        assert f.contains("origin=SecureDrop,codename=${distro_codename}")


@pytest.mark.parametrize('option', [
  'APT::Periodic::Update-Package-Lists "1";',
  'APT::Periodic::Unattended-Upgrade "1";',
  'APT::Periodic::AutocleanInterval "1";',
 ])
def test_auto_upgrades_config(host, option):
    """
    Ensures the 20auto-upgrades config is correct only under Ubuntu Focal
    """
    f = host.file('/etc/apt/apt.conf.d/20auto-upgrades')
    if host.system_info.codename == "xenial":
        assert not f.exists
    else:
        assert f.is_file
        assert f.user == "root"
        assert f.mode == 0o644
        assert f.contains('^{}$'.format(option))


def test_unattended_upgrades_functional(host):
    """
    Ensure unatteded-upgrades completes successfully and ensures all packages
    are up-to-date.
    """
    if host.system_info.codename != "xenial":
        c = host.run('sudo unattended-upgrades -d')
        assert c.rc == 0
        expected_origins = (
            "Allowed origins are: origin=Ubuntu,archive=focal, origin=Ubuntu,archive=focal-security"
            ", origin=Ubuntu,archive=focal-updates, origin=SecureDrop,codename=focal"
        )
        expected_result = (
            "No packages found that can be upgraded unattended and no pending auto-removals"
        )

        assert expected_origins in c.stdout
        assert expected_result in c.stdout


def test_reboot_required_cron(host):
    """
    Unatteded-upgrades does not reboot the system if the updates don't require it.
    However, we use daily reboots for SecureDrop to ensure memory is cleared periodically.
    Here, we ensure that reboot-required flag is dropped twice daily to ensure the system
    is rebooted every day at the scheduled time.
    """
    if host.system_info.codename != "xenial":
        with host.sudo():
            cronlist = host.run("crontab -l").stdout
            cronjob = "* */12 * * * touch /var/run/reboot-required"
            assert cronjob in cronlist


def test_all_packages_updated(host):
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
