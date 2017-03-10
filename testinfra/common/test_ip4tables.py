import pytest


securedrop_test_vars = pytest.securedrop_test_vars


def test_iptables_rules(Command, Sudo):
    """
    Ensure the correct iptables rules are checked. Using a single string
    equivalency check for the entirety of the iptables output, since
    rule order is critical. Testinfra will provide diffed output on failure.
    """
    # This approach will only work with the local Vagrant environment.
    # The hardcoded rules in per-host vars files contain static IPv4 addresses
    # that won't work in CI. TODO: update to use dynamic vars for real IPv4
    # addresses. There's a test in `mon/test_network` currently marked as "skip"
    # that includes most of the logic necessary for dynamic vars.
    with Sudo():
        c = Command("iptables -S")
        assert c.stdout == securedrop_test_vars.iptables_complete_ruleset
        assert c.rc == 0
