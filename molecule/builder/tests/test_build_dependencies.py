import pytest


testinfra_hosts = ['docker://trusty-sd-app']


def test_pip_wheel_installed(Command):
    """
    Ensure `wheel` is installed via pip, for packaging Python
    dependencies into a Debian package.
    """
    c = Command("pip freeze")
    assert "wheel==0.24.0" in c.stdout
    assert c.rc == 0


def test_sass_gem_installed(Command):
    """
    Ensure the `sass` Ruby gem is installed, for compiling SASS to CSS.
    """
    c = Command("gem list")
    assert "sass (3.4.23)" in c.stdout
    assert c.rc == 0


def test_pip_dependencies_installed(Command):
    """
    Ensure the development pip dependencies are installed
    """
    c = Command("pip list installed")
    assert "Flask-Babel" in c.stdout
    assert c.rc == 0


@pytest.mark.xfail(reason="This check conflicts with the concept of pegging"
                          "dependencies")
def test_build_all_packages_updated(Command):
    """
    Ensure a dist-upgrade has already been run, by checking that no
    packages are eligible for upgrade currently. This will ensure that
    all upgrades, security and otherwise, have been applied to the VM
    used to build packages.
    """
    c = Command('aptitude --simulate -y dist-upgrade')
    assert c.rc == 0
    assert "No packages will be installed, upgraded, or removed." in c.stdout
