import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "devops/scripts/boot-strap-venv.sh"


def run_bootstrap(
    command: str,
    *,
    cwd: Path,
    virtual_env: str = "",
    path: str | None = None,
    interactive: bool = False,
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = virtual_env
    if path is not None:
        env["PATH"] = path
    bash_arguments = ["/bin/bash", "--noprofile", "--norc", "-ic" if interactive else "-c"]
    return subprocess.run(
        [*bash_arguments, f'source "{SCRIPT}"; {command}'],
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def make_fake_venv(path: Path, version: str) -> None:
    python = path / "bin/python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/bin/sh\necho {version}\n")
    python.chmod(0o755)


def test_get_venv_version_includes_minor_version(tmp_path: Path) -> None:
    result = run_bootstrap(f'get_venv_version "{sys.prefix}"', cwd=tmp_path)

    assert result.returncode == 0
    assert result.stdout.strip() == "3.12"


def test_compatible_active_venv_is_accepted(tmp_path: Path) -> None:
    result = run_bootstrap("virtualenv_bootstrap", cwd=tmp_path, virtual_env=sys.prefix)

    assert result.returncode == 0
    assert "Using active Python 3.12 virtualenv" in result.stdout


def test_incompatible_active_venv_is_rejected(tmp_path: Path) -> None:
    venv = tmp_path / "active"
    make_fake_venv(venv, "3.11")

    result = run_bootstrap("virtualenv_bootstrap", cwd=tmp_path, virtual_env=str(venv))

    assert result.returncode == 1
    assert "Active virtualenv uses Python 3.11." in result.stdout
    assert "Python 3.12 is required." in result.stdout


def test_incompatible_active_venv_is_rejected_in_interactive_shell(tmp_path: Path) -> None:
    venv = tmp_path / "active"
    make_fake_venv(venv, "3.11")

    result = run_bootstrap(
        "virtualenv_bootstrap", cwd=tmp_path, virtual_env=str(venv), interactive=True
    )

    assert result.returncode == 1
    assert "Active virtualenv uses Python 3.11." in result.stdout
    assert "Python 3.12 is required." in result.stdout


def test_incompatible_default_venv_is_rejected(tmp_path: Path) -> None:
    make_fake_venv(tmp_path / ".venv", "3.11")

    result = run_bootstrap("virtualenv_bootstrap", cwd=tmp_path)

    assert result.returncode == 1
    assert ".venv uses Python 3.11." in result.stdout
    assert "Python 3.12 is required." in result.stdout


def test_missing_python_312_is_rejected(tmp_path: Path) -> None:
    result = run_bootstrap("virtualenv_bootstrap", cwd=tmp_path, path=str(tmp_path))

    assert result.returncode == 1
    assert "Python 3.12 is required." in result.stdout
    assert not (tmp_path / ".venv").exists()
