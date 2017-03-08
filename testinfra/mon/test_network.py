import os
import difflib
import pytest
from jinja2 import Template
from .constants import *

def determine_app_ip(SystemInfo, Command):
    """ 
    Dumb logic to determine environment and lookup relevant app IP address
    """
    app_hostname = "app"
    hostname = SystemInfo.hostname
    if "staging" in hostname:
        app_hostname = "app-staging"
    app_ip = Command.check_output("getent hosts "+app_hostname+" | awk '{ print $1 }'")
    return app_ip

def test_mon_iptables_rules(SystemInfo, Command, Sudo, Ansible):
    app_ip = determine_app_ip(SystemInfo, Command)

    # Build a dict of variables to pass to jinja for iptables comparison
    kwargs = dict(
        app_ip=app_ip,
        default_interface = Ansible("setup")["ansible_facts"]["ansible_default_ipv4"]["interface"],
        tor_user_id = Command.check_output("id -u debian-tor"),
        ssh_group_gid = Command.check_output("getent group ssh | cut -d: -f3"),
        postfix_user_id = Command.check_output("id -u postfix"),
        dns_server = DNS_SERVER)

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

@pytest.mark.parametrize('unwanted_rule', UNWANTED_IPTABLES_RULES)
def test_ensure_absent_iptables_rules(Command, SystemInfo, Sudo, unwanted_rule):
    """ Ensure that iptables rules defined do not exist on the server """
    app_ip = determine_app_ip(SystemInfo, Command)

    with Sudo():
        rule = unwanted_rule.format(app_ip=app_ip)
        assert rule not in Command.check_output("iptables-save")


@pytest.mark.parametrize('ossec_service', OSSEC_LISTENING_SERVICES)
def test_listening_ports(Socket, Sudo, ossec_service):
    print ossec_service
    socket = "{proto}://{host}:{port}".format(**ossec_service)
    with Sudo():
        assert Socket(socket).is_listening
