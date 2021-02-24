import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_ip6tables_drop_everything_xenial(host):
    """
    Ensure that all IPv6 packets are dropped by default.
    The IPv4 rules are more complicated, and tested separately.
    This test is Xenial-specific, given that on Focal we disable
    IPv6 functionality completely.
    """
    if host.system_info.codename != "xenial":
        return True
    desired_ip6tables_output = """
-P INPUT DROP
-P FORWARD DROP
-P OUTPUT DROP
""".lstrip().rstrip()

    with host.sudo():
        c = host.check_output("ip6tables -S")
        assert c == desired_ip6tables_output


def test_ip6tables_drop_everything_focal(host):
    """
    Ensures that IPv6 firewall settings are inaccessible,
    due to fully disabling IPv6 functionality at boot-time,
    via boot options.
    """
    if host.system_info.codename != "focal":
        return True
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
