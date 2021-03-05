import pytest
import re

import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_automatic_updates_dependencies(host):
    """
    Ensure critical packages are installed. If any of these are missing,
    the system will fail to receive automatic updates.
    """
    apt_dependencies = {
        'xenial': ['cron-apt', 'ntp'],
        'focal': ['cron-apt']
    }

    assert host.package("cron-apt").is_installed


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
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    if host.system_info.codename == "xenial":
        repo_config = str('update -o quiet=2'
                          ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                          ' -o Dir::Etc::SourceParts=""')
        assert f.contains('^{}$'.format(repo_config))
    else:
        repo_config = str('update -o quiet=2'
                          ' -o Dir::Etc::SourceParts=""')
        assert f.contains('^{}$'.format(repo_config))


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
    if host.system_info.codename == "xenial":
        command = str('remove -y'
                      ' linux-image-generic-lts-xenial linux-image-.*generic'
                      ' -o quiet=2')
        assert f.contains('^{}$'.format(command))
    else:
        command = str('remove -y'
                      ' linux-virtual linux-generic linux-image-.*generic'
                      ' -o quiet=2')
        assert f.contains('^{}$'.format(command))


def test_cron_apt_repo_config_upgrade(host):
    """
    Ensure cron-apt upgrades packages from the security.list config.
    """
    if host.system_info.codename == "xenial":
        f = host.file("/etc/cron-apt/action.d/5-security")
    else:
        f = host.file("/etc/cron-apt/action.d/5-upgrade")
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    assert f.contains('^autoclean -y$')
    if host.system_info.codename == "xenial":
        repo_config = str('dist-upgrade -y -o APT::Get::Show-Upgraded=true'
                          ' -o Dir::Etc::SourceList=/etc/apt/security.list'
                          ' -o Dpkg::Options::=--force-confdef'
                          ' -o Dpkg::Options::=--force-confold')
        assert f.contains(re.escape(repo_config))
    else:
        repo_config = str('dist-upgrade -y -o APT::Get::Show-Upgraded=true'
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


apt_config_options = {
    "APT::Install-Recommends": "false",
    "Dpkg::Options": [
        "--force-confold",
        "--force-confdef",
    ],
    "APT::Periodic::Update-Package-Lists": "0",
    "APT::Periodic::Unattended-Upgrade": "0",
    "APT::Periodic::AutocleanInterval": "0",
}


@pytest.mark.parametrize("k, v", apt_config_options.items())
def test_unattended_upgrades_config(host, k, v):
    """
    Ensures apt configuration is as expected.
    """
    # Dump apt config to inspect end state, apt will build config
    # from all conf files on disk, e.g. 80securedrop.
    c = host.run("apt-config dump --format '%v%n' {}".format(k))
    assert c.rc == 0
    # Some values are lists, so support that in the params
    if hasattr(v, "__getitem__"):
        for i in v:
            assert i in c.stdout
    else:
        assert v in c.stdout


def test_reboot_required_cron(host):
    """
    Legacy check, ensures that a reboot-flag cron job does not exist.
    Was briefly used to configure unattended-upgrades.
    """
    f = host.file('/etc/cron.d/reboot-flag')
    assert not f.exists


def test_all_packages_updated(host):
    """
    Ensure a dist-upgrade has already been run, by checking that no
    packages are eligible for upgrade currently.
    """
    c = host.run('apt-get dist-upgrade --simulate')
    assert c.rc == 0
    # Staging hosts will have locally built deb packages, marked as held.
    # Staging and development will have a version-locked Firefox pinned for
    # Selenium compatibility; if the holds are working, they shouldn't be
    # upgraded.
    # Example output:
    #   0 upgraded, 0 newly installed, 0 to remove and 1 not upgraded.
    # Don't test for the "not upgraded" because those map to held packages.
    assert "0 upgraded, 0 newly installed, 0 to remove" in c.stdout
