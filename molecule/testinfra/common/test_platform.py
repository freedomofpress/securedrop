import testutils

test_vars = testutils.securedrop_test_vars
testinfra_hosts = [test_vars.app_hostname, test_vars.monitor_hostname]

# We expect Ubuntu Xenial
SUPPORTED_CODENAMES = ('xenial', 'focal')
SUPPORTED_RELEASES = ('16.04', '20.04')


def test_ansible_version(host):
    """
    Check that a supported version of Ansible is being used.

    The project has long used the Ansible 1.x series, ans now
    requires the 2.x series starting with the 0.4 release. Ensure
    installation is not being performed with an outdated ansible version.
    """
    localhost = host.get_host("local://")
    c = localhost.check_output("ansible --version")
    assert c.startswith("ansible 2.")


def test_platform(host):
    """
    SecureDrop requires Ubuntu Ubuntu 16.04 or 20.04 LTS
    """
    assert host.system_info.type == "linux"
    assert host.system_info.distribution == "ubuntu"
    assert host.system_info.codename in SUPPORTED_CODENAMES
    assert host.system_info.release in SUPPORTED_RELEASES
