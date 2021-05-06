import pytest
import re


import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]


def test_fpf_apt_repo_present(host):
    """
    Ensure the FPF apt repo, apt.freedom.press, is configured.
    This repository is necessary for the SecureDrop Debian packages,
    including:

      * securedrop-app-code
      * securedrop-keyring
      * securedrop-grsec

    Depending on the host, additional FPF-maintained packages will be
    installed, e.g. for OSSEC. Install state for those packages
    is tested separately.
    """

    # If the var fpf_apt_repo_url test var is apt-test, validate that the
    # apt repository is configured on the host
    if test_vars.fpf_apt_repo_url == "https://apt-test.freedom.press":
        f = host.file('/etc/apt/sources.list.d/apt_test_freedom_press.list')
    else:
        f = host.file('/etc/apt/sources.list.d/apt_freedom_press.list')
    repo_regex = r'^deb \[arch=amd64\] {} {} main$'.format(
                      re.escape(test_vars.fpf_apt_repo_url),
                      re.escape(host.system_info.codename))
    assert f.contains(repo_regex)


def test_fpf_apt_repo_fingerprint(host):
    """
    Ensure the FPF apt repo has the correct fingerprint on the associated
    signing pubkey. Recent key rotations have taken place in:

      * 2016-10
      * 2021-06

    So let's make sure that the fingerprints accepted by the system covers both
    in the interim.
    """

    c = host.run('apt-key finger')

    fpf_gpg_pub_key_info_old = "2224 5C81 E3BA EB41 38B3  6061 310F 5612 00F4 AD77"
    fpf_gpg_pub_key_info_new = "2359 E653 8C06 13E6 5295  5E6C 188E DD3B 7B22 E6A3"

    assert c.rc == 0
    assert fpf_gpg_pub_key_info_old in c.stdout
    assert fpf_gpg_pub_key_info_new in c.stdout


@pytest.mark.parametrize('old_pubkey', [
    'pub   4096R/FC9F6818 2014-10-26 [expired: 2016-10-27]',
    'pub   4096R/00F4AD77 2016-10-20 [expires: 2017-10-20]',
    'pub   4096R/00F4AD77 2016-10-20 [expired: 2017-10-20]',
    'uid                  Freedom of the Press Foundation Master Signing Key',
    'B89A 29DB 2128 160B 8E4B  1B4C BADD E0C7 FC9F 6818',
])
def test_fpf_apt_repo_old_pubkeys_absent(host, old_pubkey):
    """
    Ensure that expired (or about-to-expire) public keys for the FPF
    apt repo are NOT present. Updates to the securedrop-keyring package
    should enforce clobbering of old pubkeys, and this check will confirm
    absence.
    """
    c = host.run('apt-key finger')
    assert old_pubkey not in c.stdout
