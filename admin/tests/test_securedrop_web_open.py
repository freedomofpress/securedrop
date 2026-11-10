import os
import platform
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "bin/securedrop-web-open"
ONION = "a" * 56 + ".onion"
SYSTEM_TOR_ENV = "none 127.0.0.1 9050"

pytestmark = pytest.mark.skipif(
    os.path.exists("/usr/local/bin/tor-browser"),
    reason="Tails tor-browser wrapper takes precedence",
)


def make_stub(path: Path) -> None:
    """Write an executable that records its name, arguments, and tor env vars"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'#!/bin/sh\necho "{path.name} $@"\necho "$TOR_PROVIDER $TOR_SOCKS_HOST $TOR_SOCKS_PORT"\n'
    )
    path.chmod(0o755)


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    config = tmp_path / ".config/securedrop-admin"
    config.mkdir(parents=True)
    (config / "app-sourcev3-ths").write_text(f"{ONION}\n")
    (config / "app-journalist.auth_private").write_text(f"{'a' * 56}:descriptor:x25519:SECRET\n")

    bindir = tmp_path / "bin"
    make_stub(bindir / "torbrowser-launcher")
    return {**os.environ, "HOME": str(tmp_path), "PATH": f"{bindir}:{os.environ['PATH']}"}


def run(env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPT), *args], env=env, capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize("interface", ["source", "journalist"])
def test_falls_back_to_torbrowser_launcher(env: dict[str, str], interface: str) -> None:
    result = run(env, interface)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"torbrowser-launcher {ONION}", SYSTEM_TOR_ENV]


@pytest.mark.parametrize("interface", ["source", "journalist"])
def test_uses_installed_tor_browser(env: dict[str, str], interface: str) -> None:
    make_stub(
        Path(env["HOME"])
        / ".local/share/torbrowser/tbb"
        / platform.machine()
        / "tor-browser/Browser/start-tor-browser"
    )
    result = run(env, interface)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"start-tor-browser --detach {ONION}", SYSTEM_TOR_ENV]


@pytest.mark.parametrize("args", [[], ["bogus"], ["source", "extra"]])
def test_usage(env: dict[str, str], args: list[str]) -> None:
    result = run(env, *args)
    assert result.returncode == 1
    assert "Usage:" in result.stderr


def test_invalid_onion(env: dict[str, str]) -> None:
    (Path(env["HOME"]) / ".config/securedrop-admin/app-sourcev3-ths").write_text("nope\n")
    result = run(env, "source")
    assert result.returncode == 1
    assert "could not parse" in result.stderr
