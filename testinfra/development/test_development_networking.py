import pytest
import os

hostenv = os.environ['SECUREDROP_TESTINFRA_TARGET_HOST']


@pytest.mark.skipif(hostenv == 'travis',
                    reason="Custom networking in Travis")
def test_development_iptables_rules(Command, Sudo):
    """
    Declare desired iptables rules
    The 'development' machine doesn't have any custom
    iptables rules, so just check for the default chains.
    """
    desired_iptables_rules = [
      '-P INPUT ACCEPT',
      '-P FORWARD ACCEPT',
      '-P OUTPUT ACCEPT',
    ]
    with Sudo():
        c = Command.check_output('iptables -S')
    for rule in desired_iptables_rules:
        assert rule in c

    # If any iptables rules are ever added, this test will
    # fail, so tests can be written for the new rules.
    # Counting newlines in the output simply to avoid calling
    # `iptables -S` again and piping to `wc -l`.
    assert c.count("\n") == len(desired_iptables_rules) - 1


def test_development_ssh_listening(Socket):
    """
    Check for ssh listening on all interfaces. In prod environment,
    SSH will be listening only on localhost, i.e. SSH over ATHS.
    """
    s = Socket("tcp://0.0.0.0:22")
    assert s.is_listening


def test_development_redis_worker(Socket):
    """
    Ensure that Redis worker is listening on localhost.
    This worker is used to handle incoming submissions.
    """

    s = Socket("tcp://127.0.0.1:6379")
    assert s.is_listening

# The Flask runners for the source and journalist interfaces
# aren't configured to run by default, e.g. on boot. Nor
# do the app tests cause them to be run. So, we shouldn't
# really expected them to be running.
# check for source interface flask port listening
# describe port(8080) do
#  it { should be_listening.on('0.0.0.0').with('tcp') }
# end
#
# check for journalist interface flask port listening
# describe port(8081) do
#  it { should be_listening.on('0.0.0.0').with('tcp') }
# end
