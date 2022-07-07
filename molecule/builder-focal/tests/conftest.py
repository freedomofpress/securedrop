"""
Import variables from vars.yml and inject into testutils namespace
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def securedrop_root() -> Path:
    """
    Returns the root of the SecureDrop working tree for the test session.
    """
    return Path(
        subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE, check=True)
        .stdout.decode("utf-8")
        .strip()
    )
