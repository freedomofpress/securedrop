import io
import os
import difflib
import pytest
from jinja2 import Template


testinfra_hosts = ["mon-staging"]
securedrop_test_vars = pytest.securedrop_test_vars


def test_mon_iptables_rules(host):

    # Build a dict of variables to pass to jinja for iptables comparison
    kwargs = dict(
        app_ip=os.environ.get('APP_IP', securedrop_test_vars.app_ip),
        default_interface=host.check_output(
            "ip r | head -n 1 | awk '{ print $5 }'"),
        tor_user_id=host.check_output("id -u debian-tor"),
        ssh_group_gid=host.check_output("getent group ssh | cut -d: -f3"),
        postfix_user_id=host.check_output("id -u postfix"),
        dns_server=securedrop_test_vars.dns_server)

    # Build iptables scrape cmd, purge comments + counters
    iptables = r"iptables-save | sed 's/ \[[0-9]*\:[0-9]*\]//g' | egrep -v '^#'"
    environment = os.environ.get("CI_SD_ENV", "staging")
    iptables_file = "{}/iptables-mon-{}.j2".format(
        os.path.dirname(os.path.abspath(__file__)),
        environment)

    # template out a local iptables jinja file
    jinja_iptables = Template(io.open(iptables_file, 'r').read())
    iptables_expected = jinja_iptables.render(**kwargs)

    with host.sudo():
        # Actually run the iptables scrape command
        iptables = host.check_output(iptables)
        # print diff comparison (only shows up in pytests if test fails or
        # verbosity turned way up)
        for iptablesdiff in difflib.context_diff(iptables_expected.split('\n'),
                                                 iptables.split('\n')):
            print(iptablesdiff)
        # Conduct the string comparison of the expected and actual iptables
        # ruleset
        assert iptables_expected == iptables


@pytest.mark.parametrize('ossec_service', [
    dict(host="0.0.0.0", proto="tcp", port=22, listening=True),
    dict(host="0.0.0.0", proto="udp", port=1514, listening=True),
    dict(host="0.0.0.0", proto="tcp", port=1515, listening=False),
])
def test_listening_ports(host, ossec_service):
    """
    Ensure the OSSEC-related services are listening on the
    expected sockets. Services to check include ossec-remoted
    and ossec-authd. Helper services such as postfix are checked
    separately.

    Note that the SSH check will fail if run against a prod host, due
    to the SSH-over-Tor strategy. We can port the parametrized values
    to config test YAML vars at that point.
    """
    socket = "{proto}://{host}:{port}".format(**ossec_service)
    with host.sudo():
        # Really hacky work-around for bug found in testinfra 1.12.0
        # https://github.com/philpep/testinfra/issues/311
        if "udp" in socket:
            lsof_socket = "{proto}@{host}:{port}".format(**ossec_service)
            udp_check = host.run("lsof -n -i"+lsof_socket)

            if ossec_service['listening']:
                assert udp_check.rc == 0
            else:
                assert udp_check.rc == 1
        else:
            assert (host.socket(socket).is_listening ==
                    ossec_service['listening'])
