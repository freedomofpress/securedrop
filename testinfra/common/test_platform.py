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


def test_platform(SystemInfo):
    """
    SecureDrop requires Ubuntu Trusty 14.04 LTS. The shelf life
    of that release means we'll need to migrate to Xenial LTS
    at some point; until then, require hosts to be running
    Ubuntu.
    """
    assert SystemInfo.type == "linux"
    assert SystemInfo.distribution == "ubuntu"
    assert SystemInfo.codename == "trusty"
    assert SystemInfo.release == "14.04"
