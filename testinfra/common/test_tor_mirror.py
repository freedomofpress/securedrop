import os
import pytest


@pytest.mark.skipif(
        os.environ.get('CIRCLE_BRANCH', 'na').startswith('release'),
        reason="Release branches will use tor-apt-test repo")
def test_tor_mirror_present(host):
    """
    Ensure the FPF mirror of the Tor apt repo, tor-apt.freedom.press,
    is configured. This repository required manual updating with current
    tor releases, to avoid breakage of untested updates.
    """
    f = '/etc/apt/sources.list.d/tor_apt_freedom_press.list'

    regex = ('^deb https:\/\/tor-apt\.freedom\.press trusty main$')
    assert host.file(f).contains(regex)


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
    assert c.stderr.rstrip() == error_text


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


@pytest.mark.parametrize('filename', [
    '/etc/apt/security.list',
    '/etc/apt/sources.list.d',
])
def test_tor_project_repo_absent(host, filename):
    """
    Ensure that no apt source list files contain the entry for
    the official Tor apt repo, since we don't control issuing updates
    in that repo. We're mirroring it to avoid breakage caused by
    untested updates (which has broken prod twice to date).
    """
    c = host.run("grep -riP 'deb\.torproject\.org' {}".format(filename))
    # Grep returns non-zero when no matches, and we want no matches.
    assert c.rc != 0
    assert c.stdout == ""


def test_tor_project_repo_files_absent(host):
    """
    Ensure that specific apt source list files are absent,
    having been 'hidden' via the securedrop-config package.
    """
    f = "/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list"
    assert not host.file(f).exists
