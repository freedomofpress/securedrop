import pytest
import os


SECUREDROP_TARGET_PLATFORM = os.environ.get("SECUREDROP_TARGET_PLATFORM", "trusty")
testinfra_hosts = [
        "docker://{}-sd-app".format(SECUREDROP_TARGET_PLATFORM)
]


def test_pip_wheel_installed(host):
    """
    Ensure `wheel` is installed via pip, for packaging Python
    dependencies into a Debian package.
    """
    c = host.run("pip list installed")
    assert "wheel" in c.stdout
    assert c.rc == 0


def test_sass_gem_installed(host):
    """
    Ensure the `sass` Ruby gem is installed, for compiling SASS to CSS.
    """
    c = host.run("gem list")
    assert "sass (3.4.23)" in c.stdout
    assert c.rc == 0


def test_pip_dependencies_installed(host):
    """
    Ensure the development pip dependencies are installed
    """
    c = host.run("pip list installed")
    assert "Flask-Babel" in c.stdout
    assert c.rc == 0


@pytest.mark.xfail(reason="This check conflicts with the concept of pegging"
                          "dependencies")
def test_build_all_packages_updated(host):
    """
    Ensure a dist-upgrade has already been run, by checking that no
    packages are eligible for upgrade currently. This will ensure that
    all upgrades, security and otherwise, have been applied to the VM
    used to build packages.
    """
    c = host.run('aptitude --simulate -y dist-upgrade')
    assert c.rc == 0
    assert "No packages will be installed, upgraded, or removed." in c.stdout
