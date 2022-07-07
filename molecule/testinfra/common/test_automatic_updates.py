import re

import pytest
import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]

# Updates and upgrades are scheduled at set times before a scheduled reboot
OFFSET_UPDATE = 2
OFFSET_UPGRADE = 1


def test_automatic_updates_dependencies(host):
    """
    Ensure critical packages are installed. If any of these are missing,
    the system will fail to receive automatic updates.
    In Focal, the apt config uses unattended-upgrades.
    """
    assert host.package("unattended-upgrades").is_installed
    assert not host.package("cron-apt").is_installed
    assert not host.package("ntp").is_installed


def test_cron_apt_config(host):
    """
    Ensure custom cron-apt config is absent, as of Focal
    """
    assert not host.file("/etc/cron-apt/config").exists
    assert not host.file("/etc/cron-apt/action.d/0-update").exists
    assert not host.file("/etc/cron-apt/action.d/5-security").exists
    assert not host.file("/etc/cron-apt/action.d/9-remove").exists
    assert not host.file("/etc/cron.d/cron-apt").exists
    assert not host.file("/etc/apt/security.list").exists
    assert not host.file("/etc/cron-apt/action.d/3-download").exists


@pytest.mark.parametrize(
    "repo",
    [
        "deb http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security main",
        "deb http://security.ubuntu.com/ubuntu {securedrop_target_platform}-security universe",
        "deb http://archive.ubuntu.com/ubuntu/ {securedrop_target_platform}-updates main",
        "deb http://archive.ubuntu.com/ubuntu/ {securedrop_target_platform} main",
    ],
)
def test_sources_list(host, repo):
    """
    Ensure the correct apt repositories are specified
    in the sources.list for apt.
    """
    repo_config = repo.format(securedrop_target_platform=host.system_info.codename)
    f = host.file("/etc/apt/sources.list")
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    repo_regex = "^{}$".format(re.escape(repo_config))
    assert f.contains(repo_regex)


apt_config_options = {
    "APT::Install-Recommends": "false",
    "Dpkg::Options": [
        "--force-confold",
        "--force-confdef",
    ],
    "APT::Periodic::Update-Package-Lists": "1",
    "APT::Periodic::Unattended-Upgrade": "1",
    "APT::Periodic::AutocleanInterval": "1",
    "APT::Periodic::Enable": "1",
    "Unattended-Upgrade::AutoFixInterruptedDpkg": "true",
    "Unattended-Upgrade::Automatic-Reboot": "true",
    "Unattended-Upgrade::Automatic-Reboot-Time": "{}:00".format(test_vars.daily_reboot_time),
    "Unattended-Upgrade::Automatic-Reboot-WithUsers": "true",
    "Unattended-Upgrade::Origins-Pattern": [
        "origin=${distro_id},archive=${distro_codename}",
        "origin=${distro_id},archive=${distro_codename}-security",
        "origin=${distro_id},archive=${distro_codename}-updates",
        "origin=SecureDrop,codename=${distro_codename}",
    ],
}


@pytest.mark.parametrize("k, v", apt_config_options.items())
def test_unattended_upgrades_config(host, k, v):
    """
    Ensures the apt and unattended-upgrades config is correct only under Ubuntu Focal
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


def test_unattended_securedrop_specific(host):
    """
    Ensures the 80securedrop config is correct. Under Ubuntu Focal,
    it will include unattended-upgrade settings. Under all hosts,
    it will disable installing 'recommended' packages.
    """
    f = host.file("/etc/apt/apt.conf.d/80securedrop")
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644
    assert f.contains('APT::Install-Recommends "false";')
    assert f.contains("Automatic-Reboot-Time")


def test_unattended_upgrades_functional(host):
    """
    Ensure unatteded-upgrades completes successfully and ensures all packages
    are up-to-date.
    """
    c = host.run("sudo unattended-upgrades --dry-run --debug")
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


@pytest.mark.parametrize(
    "service",
    [
        "apt-daily",
        "apt-daily.timer",
        "apt-daily-upgrade",
        "apt-daily-upgrade.timer",
    ],
)
def test_apt_daily_services_and_timers_enabled(host, service):
    """
    Ensure the services and timers used for unattended upgrades are enabled
    in Ubuntu 20.04 Focal.
    """
    with host.sudo():
        # The services are started only when the upgrades are being performed.
        s = host.service(service)
        assert s.is_enabled


def test_apt_daily_timer_schedule(host):
    """
    Timer for running apt-daily, i.e. 'apt-get update', should be OFFSET_UPDATE hrs
    before the daily_reboot_time.
    """
    t = (int(test_vars.daily_reboot_time) - OFFSET_UPDATE) % 24
    c = host.run("systemctl show apt-daily.timer")
    assert "TimersCalendar={ OnCalendar=*-*-* " + "{:02d}".format(t) + ":00:00 ;" in c.stdout
    assert "RandomizedDelayUSec=20m" in c.stdout


def test_apt_daily_upgrade_timer_schedule(host):
    """
    Timer for running apt-daily-upgrade, i.e. 'apt-get upgrade', should be OFFSET_UPGRADE hrs
    before the daily_reboot_time, and 1h after the apt-daily time.
    """
    t = (int(test_vars.daily_reboot_time) - OFFSET_UPGRADE) % 24
    c = host.run("systemctl show apt-daily-upgrade.timer")
    assert "TimersCalendar={ OnCalendar=*-*-* " + "{:02d}".format(t) + ":00:00 ;" in c.stdout
    assert "RandomizedDelayUSec=20m" in c.stdout


def test_reboot_required_cron(host):
    """
    Unatteded-upgrades does not reboot the system if the updates don't require it.
    However, we use daily reboots for SecureDrop to ensure memory is cleared periodically.
    Here, we ensure that reboot-required flag is dropped twice daily to ensure the system
    is rebooted every day at the scheduled time.
    """
    f = host.file("/etc/cron.d/reboot-flag")
    assert f.is_file
    assert f.user == "root"
    assert f.mode == 0o644

    line = "^{}$".format(re.escape("0 */12 * * * root touch /var/run/reboot-required"))
    assert f.contains(line)


def test_all_packages_updated(host):
    """
    Ensure a safe-upgrade has already been run, by checking that no
    packages are eligible for upgrade currently.

    The Ansible config installs a specific, out-of-date version of Firefox
    for use with Selenium. Therefore apt will report it's possible to upgrade
    Firefox, which we'll need to mark as "OK" in terms of the tests.
    """
    c = host.run("apt-get dist-upgrade --simulate")
    assert c.rc == 0
    # Staging hosts will have locally built deb packages, marked as held.
    # Staging and development will have a version-locked Firefox pinned for
    # Selenium compatibility; if the holds are working, they shouldn't be
    # upgraded.
    # Example output:
    #   0 upgraded, 0 newly installed, 0 to remove and 1 not upgraded.
    # Don't test for the "not upgraded" because those map to held packages.
    assert "0 upgraded, 0 newly installed, 0 to remove" in c.stdout
