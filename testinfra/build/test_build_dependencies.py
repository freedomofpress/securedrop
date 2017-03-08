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
            )
    build_directories = [d.format(**substitutions) for d in securedrop_test_vars.build_directories]
    return build_directories


build_directories = get_build_directories()


@pytest.mark.parametrize("package", [
    "libssl-dev",
    "python-dev",
    "python-pip",
])
def test_build_dependencies(Package, package):
    """
    Ensure development apt dependencies are installed.
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


