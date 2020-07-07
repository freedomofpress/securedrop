import pytest

test_vars = pytest.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_ip6tables_drop_everything(host):
    """
    Ensure that all IPv6 packets are dropped by default.
    The IPv4 rules are more complicated, and tested separately.
    """
    desired_ip6tables_output = """
-P INPUT DROP
-P FORWARD DROP
-P OUTPUT DROP
""".lstrip().rstrip()

    with host.sudo():
        c = host.check_output("ip6tables -S")
        assert c == desired_ip6tables_output
