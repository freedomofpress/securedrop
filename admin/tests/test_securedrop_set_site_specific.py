import importlib.machinery
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

SITE_SPECIFIC = """\
app_hostname: app
config_path: /home/amnesia/.config/securedrop-admin
daily_reboot_time: 4
securedrop_app_gpg_fingerprint: 65A1B5FF195B56353CC63DFFCC40EF1228271441
securedrop_supported_locales:
- de_DE
- en_US
ssh_users: sd
"""


@pytest.fixture
def script_path() -> Path:
    return Path(__file__).parent.parent / "bin/securedrop-set-site-specific"


@pytest.fixture
def set_site_specific(script_path: Path) -> Any:
    # no .py extension, so it has to be loaded explicitly
    loader = importlib.machinery.SourceFileLoader("set_site_specific", str(script_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec:
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module
    return None


@pytest.fixture
def site_specific(tmp_path: Path) -> Path:
    path = tmp_path / "site-specific"
    path.write_text(SITE_SPECIFIC)
    path.chmod(0o600)
    return path


def run(script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script_path, *args], capture_output=True, text=True, check=False
    )


def test_replaces_value(set_site_specific: Any, site_specific: Path) -> None:
    set_site_specific.set_value(site_specific, "config_path", "/home/user/.config/securedrop-admin")

    assert site_specific.read_text() == SITE_SPECIFIC.replace("/home/amnesia/", "/home/user/")


def test_preserves_mode(set_site_specific: Any, site_specific: Path) -> None:
    set_site_specific.set_value(site_specific, "config_path", "/home/user/.config/securedrop-admin")

    assert site_specific.stat().st_mode & 0o777 == 0o600
    # no leftover temporary file
    assert list(site_specific.parent.iterdir()) == [site_specific]


def test_cli(script_path: Path, site_specific: Path) -> None:
    result = run(script_path, "--file", str(site_specific), "config_path", "/home/user/.config")

    assert result.returncode == 0, result.stderr
    assert yaml.safe_load(site_specific.read_text())["config_path"] == "/home/user/.config"


def test_cli_missing_file(script_path: Path, tmp_path: Path) -> None:
    result = run(script_path, "--file", str(tmp_path / "missing"), "config_path", "/tmp")

    assert result.returncode == 1
    assert "Error updating" in result.stderr
    assert not (tmp_path / "missing").exists()


def test_cli_disallowed_key(script_path: Path, site_specific: Path) -> None:
    result = run(script_path, "--file", str(site_specific), "ssh_users", "admin")

    assert result.returncode == 2
    assert "invalid choice: 'ssh_users'" in result.stderr
    assert site_specific.read_text() == SITE_SPECIFIC
