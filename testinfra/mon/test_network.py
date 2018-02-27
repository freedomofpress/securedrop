import pytest

securedrop_test_vars = pytest.securedrop_test_vars


@pytest.mark.parametrize('ossec_service', [
    dict(host="0.0.0.0", proto="tcp", port=22, listening=True),
    dict(host="0.0.0.0", proto="udp", port=1514, listening=True),
    dict(host="0.0.0.0", proto="tcp", port=1515, listening=False),
])
def test_listening_ports(Socket, Sudo, ossec_service):
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
    with Sudo():
        assert Socket(socket).is_listening == ossec_service['listening']
