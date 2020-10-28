"""
Import variables from vars.yml and inject into testutils namespace
"""

import os
import io
import yaml
import testutils


filepath = os.path.join(os.path.dirname(__file__), "vars.yml")
with io.open(filepath, 'r') as f:
    securedrop_test_vars = yaml.safe_load(f)

# Tack on target OS for use in tests
securedrop_target_platform = os.environ.get("SECUREDROP_TARGET_PLATFORM")
securedrop_test_vars["securedrop_target_platform"] = securedrop_target_platform

testutils.securedrop_test_vars = testutils.inject_vars(securedrop_test_vars)
