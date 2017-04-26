import pytest


def test_ansible_version(LocalCommand):
    """
    Check that a supported version of Ansible is being used.

    The project has long used the Ansible 1.x series, but aims
    to upgrade to 2.x during the 0.4 release. Developers commonly
    install a recent version of Ansible when developing SecureDrop,
    which is not a good baseline for testing.
    """
    c = LocalCommand("ansible --version")
    assert c.stdout.startswith("ansible 1.")
    assert "ansible 2" not in c.stdout


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
