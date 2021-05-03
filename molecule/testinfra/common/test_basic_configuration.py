from testinfra.host import Host

import testutils


test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_system_time(host: Host) -> None:
    assert not host.package("ntp").is_installed
    assert not host.package("ntpdate").is_installed

    s = host.service("systemd-timesyncd")
    assert s.is_running
    assert s.is_enabled
    assert not s.is_masked

    # File will be touched on every successful synchronization,
    # see 'man systemd-timesyncd'`
    assert host.file("/run/systemd/timesync/synchronized").exists

    c = host.run("timedatectl show")
    assert "NTP=yes" in c.stdout
    assert "NTPSynchronized=yes" in c.stdout
