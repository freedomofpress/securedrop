import pytest
import re


test_vars = pytest.securedrop_test_vars
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
    signing pubkey. The key changed in October 2016, so test for the
    newest fingerprint, which is installed on systems via the
    `securedrop-keyring` package.
    """

    c = host.run('apt-key finger')

    fpf_gpg_pub_key_info = """/etc/apt/trusted.gpg.d/securedrop-keyring.gpg
---------------------------------------------
pub   4096R/00F4AD77 2016-10-20 [expires: 2021-06-30]
      Key fingerprint = 2224 5C81 E3BA EB41 38B3  6061 310F 5612 00F4 AD77
uid                  SecureDrop Release Signing Key"""

    assert c.rc == 0
    assert fpf_gpg_pub_key_info in c.stdout


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
