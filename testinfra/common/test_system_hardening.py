import os
import pytest
import re

hostenv = os.environ['SECUREDROP_TESTINFRA_TARGET_HOST']


@pytest.mark.parametrize('sysctl_opt', [
  ('net.ipv4.conf.all.accept_redirects', 0),
  ('net.ipv4.conf.all.accept_source_route', 0),
  ('net.ipv4.conf.all.rp_filter', 1),
  ('net.ipv4.conf.all.secure_redirects', 0),
  ('net.ipv4.conf.all.send_redirects', 0),
  ('net.ipv4.conf.default.accept_redirects', 0),
  ('net.ipv4.conf.default.accept_source_route', 0),
  ('net.ipv4.conf.default.rp_filter', 1),
  ('net.ipv4.conf.default.secure_redirects', 0),
  ('net.ipv4.conf.default.send_redirects', 0),
  ('net.ipv4.icmp_echo_ignore_broadcasts', 1),
  ('net.ipv4.ip_forward', 0),
  ('net.ipv4.tcp_max_syn_backlog', 4096),
  ('net.ipv4.tcp_syncookies', 1),
  ('net.ipv6.conf.all.disable_ipv6', 1),
  ('net.ipv6.conf.default.disable_ipv6', 1),
  ('net.ipv6.conf.lo.disable_ipv6', 1),
])
def test_sysctl_options(Sysctl, Sudo, sysctl_opt):
    """
    Ensure sysctl flags are set correctly. Most of these checks
    are disabling IPv6 and hardening IPv4, which is appropriate
    due to the heavy use of Tor.
    """
    with Sudo():
        assert Sysctl(sysctl_opt[0]) == sysctl_opt[1]


def test_dns_setting(File):
    """
    Ensure DNS service is hard-coded in resolv.conf config.
    """
    f = File('/etc/resolvconf/resolv.conf.d/base')
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert oct(f.mode) == "0644"
    assert f.contains('^nameserver 8\.8\.8\.8$')


@pytest.mark.parametrize('kernel_module', [
    'bluetooth',
    'iwlwifi',
])
def test_blacklisted_kernel_modules(Command, File, Sudo, kernel_module):
    """
    Test that unwanted kernel modules are blacklisted on the system.
    Mostly these checks are defense-in-depth approaches to ensuring
    that wireless interfaces will not work.
    """
    with Sudo():
        assert kernel_module not in Command("lsmod").stdout

    f = File("/etc/modprobe.d/blacklist.conf")
    assert f.contains("^blacklist {}$".format(kernel_module))


@pytest.mark.skipif(hostenv.startswith('mon'),
                    reason="Monitor Server does not have swap disabled yet.")
def test_swap_disabled(Command):
    """
    Ensure swap space is disabled. Prohibit writing memory to swapfiles
    to reduce the threat of forensic analysis leaking any sensitive info.
    """
    c = Command.check_output('swapon --summary')
    # A leading slash will indicate full path to a swapfile.
    assert not re.search("^/", c, re.M)
    # Expect that ONLY the headers will be present in the output.
    rgx = re.compile("Filename\s*Type\s*Size\s*Used\s*Priority")
    assert re.search(rgx, c)
