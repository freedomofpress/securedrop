import os
import re
import subprocess
from pathlib import Path

OS_VERSION = os.environ.get("OS_VERSION", "focal")
SECUREDROP_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
)
BUILD_DIRECTORY = SECUREDROP_ROOT / f"build/{OS_VERSION}"


def test_admin_paths_are_present():
    """
    Ensures the `securedrop-admin` package contains the specified paths
    """
    wanted_files = [
        "/usr/bin/securedrop-admin",
        "/usr/bin/validate-gpg-key.sh",
        "/usr/share/securedrop-admin/ansible-base/",
        "/usr/share/securedrop-admin/translations/",
        "/usr/share/securedrop-admin/venv/",
    ]
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin_*_amd64.deb"))
    assert deb_files, "No securedrop-admin .deb file found"
    path = deb_files[0]
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    for wanted_file in wanted_files:
        assert re.search(
            rf"^.* .{wanted_file}$",
            contents,
            re.M,
        )


def test_admin_qubes_paths_are_present():
    """
    Ensures the `securedrop-admin-qubes` package contains the specified paths
    """
    wanted_files = [
        "/usr/bin/securedrop-set-site-specific",
    ]
    deb_files = list((BUILD_DIRECTORY).glob("securedrop-admin-qubes_*_amd64.deb"))
    assert deb_files, "No securedrop-admin-qubes .deb file found"
    path = deb_files[0]
    contents = subprocess.check_output(["dpkg-deb", "-c", str(path)]).decode()
    for wanted_file in wanted_files:
        assert re.search(
            rf"^.* .{wanted_file}$",
            contents,
            re.M,
        )
