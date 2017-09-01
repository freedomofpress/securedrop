import pytest


@pytest.mark.parametrize('build_path', [
    '/tmp/build-',
    '/tmp/rsync-filter',
    '/tmp/src_install_files',
    '/tmp/build-securedrop-keyring',
    '/tmp/build-securedrop-ossec-agent',
    '/tmp/build-securedrop-ossec-server',
])
def test_build_ossec_apt_dependencies(File, build_path):
    """
    Ensure that unwanted build paths are absent. Most of these were created
    as unwanted side-effects during CI-related changes to the build scripts.

    All paths are rightly considered "legacy" and should never be present on
    the build host. This test is strictly for guarding against regressions.
    """
    assert not File(build_path).exists
