def test_ip6tables_drop_everything(Command, Sudo):
    """
    Ensure that all IPv6 packets are dropped by default.
    The IPv4 rules are more complicated, and tested separately.
    """
    desired_ip6tables_output = """
-P INPUT DROP
-P FORWARD DROP
-P OUTPUT DROP
""".lstrip().rstrip()

    with Sudo():
        c = Command("ip6tables -S")
        assert c.stdout == desired_ip6tables_output
        assert c.rc == 0
