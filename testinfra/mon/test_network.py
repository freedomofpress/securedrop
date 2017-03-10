import os
import difflib
import pytest
from jinja2 import Template


securedrop_test_vars = pytest.securedrop_test_vars


def determine_app_ip(SystemInfo, Command):
    """
    Dumb logic to determine environment and lookup relevant app IP address
    """
    app_hostname = "app-prod"
    hostname = SystemInfo.hostname
    if "staging" in hostname:
        app_hostname = "app-staging"
    app_ip = Command.check_output("getent hosts "+app_hostname+" | awk '{ print $1 }'")
    return app_ip


# Skipping because the simpler string comparison check for entire output
# check is sufficient for mon-staging. On other hosts, though, we may need
# the more dynamic logic described below.
@pytest.mark.skip
def test_mon_iptables_rules(SystemInfo, Command, Sudo, Ansible):
    app_ip = determine_app_ip(SystemInfo, Command)

    # Build a dict of variables to pass to jinja for iptables comparison
    kwargs = dict(
        app_ip=app_ip,
        default_interface = Ansible("setup")["ansible_facts"]["ansible_default_ipv4"]["interface"],
        tor_user_id = Command.check_output("id -u debian-tor"),
        ssh_group_gid = Command.check_output("getent group ssh | cut -d: -f3"),
        postfix_user_id = Command.check_output("id -u postfix"),
        dns_server = securedrop_test_vars.dns_server)

    # Build iptables scrape cmd, purge comments + counters
    iptables = "iptables-save | sed 's/ \[[0-9]*\:[0-9]*\]//g' | egrep -v '^#'"
    iptables_file = "{}/iptables-{}.j2".format(
                                      os.path.dirname(os.path.abspath(__file__)),
                                      SystemInfo.hostname)

    # template out a local iptables jinja file
    jinja_iptables = Template(open(iptables_file,'r').read())
    iptables_expected = jinja_iptables.render(**kwargs)

    with Sudo():
        # Actually run the iptables scrape command
        iptables = Command.check_output(iptables)
        # print diff comparison (only shows up in pytests if test fails or
        # verbosity turned way up)
        for iptablesdiff in difflib.context_diff(iptables_expected.split('\n'),
                                             iptables.split('\n')):
            print(iptablesdiff)
        # Conduct the string comparison of the expected and actual iptables
        # ruleset
        assert iptables_expected == iptables


@pytest.mark.parametrize('ossec_service', [
    dict(host="0.0.0.0", proto="tcp", port=22),
    dict(host="127.0.0.1", proto="tcp", port=25),
    dict(host="0.0.0.0", proto="udp", port=1514),
])
def test_listening_ports(Socket, Sudo, ossec_service):
    """
    Ensure the OSSEC-related services are listening on the
    expected sockets. Services to check include ossec, mail, and ssh.
    """
    socket = "{proto}://{host}:{port}".format(**ossec_service)
    with Sudo():
        assert Socket(socket).is_listening
