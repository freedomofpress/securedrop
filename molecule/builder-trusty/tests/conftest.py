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
        securedrop_test_vars = yaml.safe_load(f)

    # Tack on target OS for use in tests
    securedrop_target_platform = os.environ.get("SECUREDROP_TARGET_PLATFORM",
                                                "trusty")
    securedrop_test_vars["securedrop_target_platform"] = securedrop_target_platform
    # Wrapping the return value to accommodate for pytest namespacing
    return dict(securedrop_test_vars=securedrop_test_vars)
