import pytest


securedrop_test_vars = pytest.securedrop_test_vars


def get_build_directories():
    """
    Helper function to retrieve module-namespace test vars and format
    the strings to interpolate version info. Keeps the test vars DRY
    in terms of version info, and required since we can't rely on
    Jinja-based evaluation of the YAML files (so we can't trivially
    reuse vars in other var values, as is the case with Ansible).
    """
    substitutions = dict(
            securedrop_version=securedrop_test_vars.securedrop_version,
            ossec_version=securedrop_test_vars.ossec_version,
            keyring_version=securedrop_test_vars.keyring_version,
            config_version=securedrop_test_vars.config_version,
            )
    build_directories = [d.format(**substitutions) for d
                         in securedrop_test_vars.build_directories]
    return build_directories


build_directories = get_build_directories()


@pytest.mark.parametrize("package", [
    "devscripts",
    "git",
    "libssl-dev",
    "python-dev",
    "python-pip",
    "secure-delete",
])
def test_build_dependencies(Package, package):
    """
    Ensure development apt dependencies are installed.
    The devscripts and git packages are required for running the
    `update_version.sh` script, which should be executed inside the
    build VM, so let's make sure they're present.
    """
    assert Package(package).is_installed


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


@pytest.mark.parametrize("directory", get_build_directories())
def test_build_directories(File, directory):
    """
    Ensure the build directories are present. These directories are
    the top-level of the Debian packages being created. They contain
    nested subdirs of varying complexity, depending on package.
    """
    if '{}' in directory:
        directory = directory.format(securedrop_test_vars.securedrop_version)
    assert File(directory).is_directory


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
