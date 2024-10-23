import os
import subprocess
import tempfile
from pathlib import Path

import pytest

UBUNTU_VERSION = os.environ.get("UBUNTU_VERSION", "focal")
SECUREDROP_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
)
DEB_PATHS = list((SECUREDROP_ROOT / f"build/{UBUNTU_VERSION}").glob("*.deb"))
PYTHON_VERSION = {"focal": "8", "noble": "12"}[UBUNTU_VERSION]
SITE_PACKAGES = f"/opt/venvs/securedrop-app-code/lib/python3.{PYTHON_VERSION}/site-packages"


@pytest.fixture(scope="module")
def securedrop_app_code_contents() -> str:
    """
    Returns the content listing of the securedrop-app-code Debian package.
    """
    try:
        path = [pkg for pkg in DEB_PATHS if pkg.name.startswith("securedrop-app-code")][0]
    except IndexError:
        raise RuntimeError("Unable to find securedrop-app-code package in build/ folder")
    return subprocess.check_output(["dpkg-deb", "--contents", path]).decode()


@pytest.mark.parametrize("deb", DEB_PATHS)
def test_deb_packages_appear_installable(deb: Path) -> None:
    """
    Confirms that a dry-run of installation reports no errors.
    Simple check for valid Debian package structure, but not thorough.
    When run on a malformed package, `dpkg` will report:

       dpkg-deb: error: `foo.deb' is not a debian format archive

    Testing application behavior is left to the functional tests.
    """

    # Normally this is called as root, but we can get away with simply
    # adding sbin to the path
    path = os.getenv("PATH") + ":/usr/sbin:/sbin"
    subprocess.check_call(["dpkg", "--install", "--dry-run", deb], env={"PATH": path})


@pytest.mark.parametrize("deb", DEB_PATHS)
def test_deb_package_contains_expected_conffiles(deb: Path):
    """
    Ensures the `securedrop-app-code` package declares only allow-listed
    `conffiles`. Several files in `/etc/` would automatically be marked
    conffiles, which would break unattended updates to critical package
    functionality such as AppArmor profiles. This test validates overrides
    in the build logic to unset those conffiles.

    The same applies to `securedrop-config` too.
    """
    if not deb.name.startswith(("securedrop-app-code", "securedrop-config")):
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.check_call(["dpkg-deb", "--control", deb, tmpdir])
        conffiles_path = Path(tmpdir) / "conffiles"
        assert conffiles_path.exists()
        # No files are currently allow-listed to be conffiles
        assert conffiles_path.read_text().rstrip() == ""


@pytest.mark.parametrize(
    "path",
    [
        "/var/www/securedrop/.well-known/pki-validation/",
        "/var/www/securedrop/translations/messages.pot",
        "/var/www/securedrop/translations/de_DE/LC_MESSAGES/messages.mo",
        f"{SITE_PACKAGES}/redwood/redwood.cpython-3{PYTHON_VERSION}-x86_64-linux-gnu.so",
    ],
)
def test_app_code_paths(securedrop_app_code_contents: str, path: str):
    """
    Ensures the `securedrop-app-code` package contains the specified paths
    """
    for line in securedrop_app_code_contents.splitlines():
        if line.endswith(path):
            assert True
            return

    pytest.fail("not found")


@pytest.mark.parametrize(
    "path",
    [
        "/var/www/securedrop/static/.webassets-cache/",
        "/var/www/securedrop/static/gen/",
        "/var/www/securedrop/config.py",
        "/var/www/securedrop/static/i/custom_logo.png",
        ".j2",
    ],
)
def test_app_code_paths_missing(securedrop_app_code_contents: str, path: str):
    """
    Ensures the `securedrop-app-code` package do *NOT* contain the specified paths
    """
    for line in securedrop_app_code_contents.splitlines():
        if line.endswith(path):
            pytest.fail(f"found {line}")
