import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("filename", ("journalist.wsgi", "source.wsgi"))
def test_wsgi(filename):
    """
    Verify that all setup code and imports in the wsgi files work

    This is slightly hacky because it executes the wsgi files using
    the current virtualenv, and we hack the paths so it works out.
    """
    sd_dir = Path(__file__).parent.parent
    wsgi = sd_dir / "debian/app-code/var/www" / filename
    python_path = os.getenv("PYTHONPATH", "")
    subprocess.check_call(
        [sys.executable, str(wsgi)], env={"PYTHONPATH": f"{python_path}:{sd_dir}"}
    )
