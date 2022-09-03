import importlib

import config as _config
from sdconfig import SecureDropConfig


def test_missing_config_attribute_is_handled():
    """
    Test handling of incomplete configurations.

    Long-running SecureDrop instances might not have ever updated
    config.py, so could be missing newer settings. This tests that
    sdconfig.SDConfig can be initialized without error with such a
    configuration.
    """
    attributes_to_test = (
        "DATABASE_ENGINE",
        "DATABASE_FILE",
        "ADJECTIVES",
        "NOUNS",
        "GPG_KEY_DIR",
        "JOURNALIST_TEMPLATES_DIR",
        "SCRYPT_PARAMS",
        "SECUREDROP_DATA_ROOT",
        "SECUREDROP_ROOT",
        "SESSION_EXPIRATION_MINUTES",
        "SOURCE_TEMPLATES_DIR",
        "TEMP_DIR",
        "STORE_DIR",
    )

    try:
        importlib.reload(_config)

        for a in attributes_to_test:
            delattr(_config, a)

        SecureDropConfig.get_current()
    finally:
        importlib.reload(_config)
