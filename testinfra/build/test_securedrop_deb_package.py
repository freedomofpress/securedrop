import pytest
import os
import re


securedrop_test_vars = pytest.securedrop_test_vars


def extract_package_name_from_filepath(filepath):
    """
    Helper function to infer intended package name from
    the absolute filepath, using a rather garish regex.
    E.g., given:
       securedrop-ossec-agent-2.8.2+0.3.10-amd64.deb

    retuns:

       securedrop-ossec-agent

    which can then be used for comparisons in dpkg output.
    """
    deb_basename = os.path.basename(filepath)
    package_name = re.search('^([a-z\-]+(?!\d))', deb_basename).groups()[0]
    assert deb_basename.startswith(package_name)
    return package_name


@pytest.mark.parametrize("deb", [
  # Test will interpolate version in filepath.
  "/vagrant/build/securedrop-app-code-{}-amd64.deb",
  "/vagrant/build/securedrop-ossec-agent-2.8.2+{}-amd64.deb",
  "/vagrant/build/securedrop-ossec-server-2.8.2+{}-amd64.deb",
])
def test_build_deb_packages(File, deb):
    """
    Sanity check the built Debian packages for Control field
    values and general package structure.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    assert deb_package.is_file


@pytest.mark.parametrize("deb", [
    # Test will interpolate version in filepath.
    "/vagrant/build/securedrop-app-code-{}-amd64.deb",
    "/vagrant/build/securedrop-ossec-agent-2.8.2+{}-amd64.deb",
    "/vagrant/build/securedrop-ossec-server-2.8.2+{}-amd64.deb",
])
def test_deb_packages_appear_installable(File, Command, Sudo, deb):
    """
    Confirms that a dry-run of installation reports no errors.
    Simple check for valid Debian package structure, but not thorough.
    When run on a malformed package, `dpkg` will report:

       dpkg-deb: error: `foo.deb' is not a debian format archive

    Testing application behavior is left to the functional tests.
    """

    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))

    deb_basename = os.path.basename(deb_package.path)
    package_name = extract_package_name_from_filepath(deb_package.path)
    assert deb_basename.startswith(package_name)

    # Sudo is required to call `dpkg --install`, even as dry-run.
    with Sudo():
        c = Command("dpkg --install --dry-run {}".format(deb_package.path))
        assert "Selecting previously unselected package {}".format(package_name) in c.stdout
        regex = "Preparing to unpack [./]+{} ...".format(re.escape(deb_basename))
        assert re.search(regex, c.stdout, re.M)
        assert c.rc == 0


@pytest.mark.parametrize("deb", [
    # Test will interpolate version in filepath.
    "/vagrant/build/securedrop-app-code-{}-amd64.deb",
    "/vagrant/build/securedrop-ossec-agent-2.8.2+{}-amd64.deb",
    "/vagrant/build/securedrop-ossec-server-2.8.2+{}-amd64.deb",
])
def test_deb_package_control_fields(File, Command, deb):
    """
    Ensure Debian Control fields are populated as expected in the package.
    These checks are rather superficial, and don't actually confirm that the
    .deb files are not broken. At a later date, consider integration tests
    that actually use these built files during an Ansible provisioning run.
    """
    deb_package = File(deb.format(
        securedrop_test_vars.securedrop_version))
    # The `--field` option will display all fields if none are specified.
    c = Command("dpkg-deb --field {}".format(deb_package.path))

    deb_basename = os.path.basename(deb_package.path)
    package_name = extract_package_name_from_filepath(deb_package.path)

    assert "Maintainer: SecureDrop Team <securedrop@freedom.press>" in c.stdout
    assert "Homepage: https://securedrop.org" in c.stdout
    assert "Architecture: amd64" in c.stdout
    assert "Package: {}".format(package_name) in c.stdout
    assert c.rc == 0
