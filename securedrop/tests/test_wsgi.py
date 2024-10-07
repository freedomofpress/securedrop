import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def _journalist_pubkey():
    """provision a valid public key for the JI startup check"""
    path = Path("/tmp/securedrop/journalist.pub")
    if not path.exists():
        created_dir = False
        try:
            if not path.parent.exists():
                path.parent.mkdir()
                created_dir = True
            shutil.copy(Path(__file__).parent / "files/test_journalist_key.pub", path)
            yield
        finally:
            if created_dir:
                shutil.rmtree(path.parent)
            else:
                path.unlink()


@pytest.mark.parametrize("filename", ["journalist.wsgi", "source.wsgi"])
def test_wsgi(filename, _journalist_pubkey):
    """
    Verify that all setup code and imports in the wsgi files work

    This is slightly hacky because it executes the wsgi files using
    the current virtualenv, and we hack the paths so it works out.
    """
    sd_dir = Path(__file__).parent.parent
    wsgi = sd_dir / "debian/app-code/var/www" / filename
    python_path = os.getenv("PYTHONPATH", "")
    subprocess.check_call(
        [sys.executable, str(wsgi)],
        env={"PYTHONPATH": f"{python_path}:{sd_dir}", "SECUREDROP_ENV": "test"},
    )
