import pytest

test_vars = pytest.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


@pytest.mark.parametrize('repo_file', [
    "/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list",
])
def test_tor_mirror_absent(host, repo_file):
    """
    Ensure that neither the Tor Project repo, nor the FPF mirror of the
    Tor Project repo, tor-apt.freedom.press, are configured. We've moved
    to hosting Tor packages inside the primary FPF apt repo.
    """
    f = host.file(repo_file)
    assert not f.exists


def test_tor_keyring_absent(host):
    """
    Tor packages are installed via the FPF apt mirror, and signed with the
    SecureDrop Release Signing Key. As such, the official Tor public key
    should *not* be present, since we don't want to install packages
    from that source.
    """
    # Can't use the TestInfra Package module to check state=absent,
    # so let's check by shelling out to `dpkg -l`. Dpkg will automatically
    # honor simple regex in package names.
    package = "deb.torproject.org-keyring"
    c = host.run("dpkg -l {}".format(package))
    assert c.rc == 1
    error_text = "dpkg-query: no packages found matching {}".format(package)
    assert error_text in c.stderr.strip()


@pytest.mark.parametrize('tor_key_info', [
    "pub   2048R/886DDD89 2009-09-04 [expires: 2020-08-29]",
    "Key fingerprint = A3C4 F0F9 79CA A22C DBA8  F512 EE8C BC9E 886D DD89",
    "deb.torproject.org archive signing key",
])
def test_tor_mirror_fingerprint(host, tor_key_info):
    """
    Legacy test. The Tor Project key was added to SecureDrop servers
    via the `deb.torproject.org-keyring` package. Since FPF started mirroring
    the official Tor apt repository, we no longer need the key to be present.

    Since the `deb.torproject.org-keyring` package is installed on already
    running instances, the public key will still be present. We'll need
    to remove those packages separately.
    """
    c = host.run('apt-key finger')
    assert c.rc == 0
    assert tor_key_info not in c.stdout


@pytest.mark.parametrize('repo_pattern', [
    'deb.torproject.org',
    'tor-apt.freedom.press',
    'tor-apt-test.freedom.press',
])
def test_tor_repo_absent(host, repo_pattern):
    """
    Ensure that no apt source list files contain the entry for
    the official Tor apt repo, since we don't control issuing updates
    in that repo. We're mirroring it to avoid breakage caused by
    untested updates (which has broken prod twice to date).
    """
    cmd = "grep -rF '{}' /etc/apt/".format(repo_pattern)
    c = host.run(cmd)
    # Grep returns non-zero when no matches, and we want no matches.
    assert c.rc != 0
    assert c.stdout == ""
