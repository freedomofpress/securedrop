"""
Import variables from vars.yml and inject into pytest namespace
"""

import os
import io
import yaml


def pytest_namespace():
    """ Return dict of vars imported as 'securedrop_test_vars' into pytest
        global namespace
    """
    filepath = os.path.join(os.path.dirname(__file__), "vars.yml")
    with io.open(filepath, 'r') as f:
        return dict(securedrop_test_vars=yaml.safe_load(f))
