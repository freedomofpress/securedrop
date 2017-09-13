import pytest


@pytest.mark.parametrize('apt_package', [
  'inotify-tools',
  'libssl-dev',
  'make',
  'tar',
  'unzip',
])
def test_build_ossec_apt_dependencies(Package, apt_package):
    """
    Ensure that the apt dependencies required for building the OSSEC
    source deb packages (not the metapackages) are installed.
    """
    assert Package(apt_package).is_installed
