import pytest
import os


SECUREDROP_TARGET_PLATFORM = os.environ.get("SECUREDROP_TARGET_PLATFORM")
SECUREDROP_PYTHON_VERSION = os.environ.get("SECUREDROP_PYTHON_VERSION", "3.5")
SECUREDROP_DH_VIRTUALENV_VERSION = os.environ.get("SECUREDROP_DH_VIRTUALENV_VERSION", "1.2.1")
testinfra_hosts = [
        "docker://{}-sd-app".format(SECUREDROP_TARGET_PLATFORM)
]


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
    c = host.run("pip3 list installed")
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


def test_python_version(host):
    """
    The Python 3 version shouldn't change between LTS releases, but we're
    pulling in some packages from Debian for dh-virtualenv support, so
    we must be careful not to change Python as well.
    """
    c = host.run("python3 --version")
    version_string = "Python {}".format(SECUREDROP_PYTHON_VERSION)
    assert c.stdout.startswith(version_string)


def test_dh_virtualenv(host):
    """
    The version of dh-virtualenv in Xenial repos isn't new enough to work
    with setuptools >= 50, so we pull it in from Debian. Confirm the expected
    recent version of dh-virtualenv is found. Since we're tracking Debian unstable
    for this dependency, this check will fail if unstable surprises us with a new
    version.
    """
    c = host.run("dh_virtualenv --version")
    version_string = "dh_virtualenv {}".format(SECUREDROP_DH_VIRTUALENV_VERSION)
    assert c.stdout.startswith(version_string)
