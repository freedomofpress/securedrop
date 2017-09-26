import pytest


def test_tor_mirror_present(File):
    """
    Ensure the FPF mirror of the Tor apt repo, tor-apt.ops.freedom.press,
    is configured. This repository required manual updating with current
    tor releases, to avoid breakage of untested updates.
    """
    f = File('/etc/apt/sources.list.d/tor_apt_ops_apt_freedom_press.list')

    regex = ('^deb http:\/\/tor-apt\.ops\.freedom\.press trusty main$')
    assert f.contains(regex)


def test_tor_mirror_fingerprint(Command):
    """
    Ensure the FPF tor mirror repo has the correct fingerprint on the
    associated signing pubkey. We don't use the SecureDrop Release Signing
    Key for the Tor mirror: packages are identical to the official Tor repo,
    so signatures match, as well.
    """
    c = Command('apt-key finger')
    tor_gpg_pub_key_info = """/etc/apt/trusted.gpg.d/deb.torproject.org-keyring.gpg
-----------------------------------------------------
pub   2048R/886DDD89 2009-09-04 [expires: 2020-08-29]
      Key fingerprint = A3C4 F0F9 79CA A22C DBA8  F512 EE8C BC9E 886D DD89
uid                  deb.torproject.org archive signing key
sub   2048R/219EC810 2009-09-04 [expires: 2018-08-30]"""

    assert c.rc == 0
    assert tor_gpg_pub_key_info in c.stdout


@pytest.mark.parametrize('filename', [
    '/etc/apt/security.list',
    '/etc/apt/sources.list.d',
])
def test_tor_project_repo_absent(Command):
    """
    Ensure that no apt source list files contain the entry for
    the official Tor apt repo, since we don't control issuing updates
    in that repo. We're mirroring it to avoid breakage caused by
    untested updates (which has broken prod twice to date).
    """
    c = Command("grep -riP 'deb\.torproject\.org' /etc/apt*")
    # Grep returns non-zero when no matches, and we want no matches.
    assert c.rc != 0
    assert c.stdout == ""


def test_tor_project_repo_files_absent(File):
    """
    Ensure that specific apt source list files are absent,
    having been 'hidden' via the securedrop-config package.
    """
    f = File("/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list")
    assert not f.exists
