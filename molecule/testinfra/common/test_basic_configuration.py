from testinfra.host import Host

import testutils


test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_system_time(host: Host) -> None:
    if host.system_info.codename == "xenial":
        assert host.package("ntp").is_installed
        assert host.package("ntpdate").is_installed

        # TODO: The staging setup timing is too erratic for the
        # following check. If we do want to reinstate it before
        # dropping Xenial support, it should be done in a loop to give
        # ntpd time to sync after the machines are created.

        # c = host.run("ntpq -c rv")
        # assert "leap_none" in c.stdout
        # assert "sync_ntp" in c.stdout
        # assert "refid" in c.stdout
    else:
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
