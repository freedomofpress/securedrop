import pytest


testinfra_hosts = ['docker://sd-builder-app']

SD_APP_VENV = "/tmp/sd-app-venv/"


def test_pip_wheel_installed(Command):
    """
    Ensure `wheel` is installed via pip, for packaging Python
    dependencies into a Debian package.
    """
    c = Command("{}/bin/pip freeze --all".format(SD_APP_VENV))
    assert "wheel==0.31.1" in c.stdout
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
    c = Command("{}/bin/pip list".format(SD_APP_VENV))
    assert "Flask-Babel" in c.stdout
    assert c.rc == 0
