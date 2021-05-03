import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_ip6tables_drop_everything_focal(host):
    """
    Ensures that IPv6 firewall settings are inaccessible,
    due to fully disabling IPv6 functionality at boot-time,
    via boot options.
    """
    with host.sudo():
        c = host.run("ip6tables -S")
        assert c.rc != 0
        assert c.stdout == ""


def test_ipv6_addresses_absent(host):
    """
    Ensure that no IPv6 addresses are assigned to interfaces.
    """
    with host.sudo():
        c = host.check_output("ip -6 addr")
        assert c == ""
