import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_system_time(host):
    if test_vars.securedrop_target_distribution == "xenial":
        c = host.run("timedatectl status")
        assert "Network time on: yes" in c.stdout
        assert "NTP synchronized: yes" in c.stdout
    else:
        c = host.run("timedatectl show")
        assert "NTP=yes" in c.stdout
        assert "NTPSynchronized=yes" in c.stdout
