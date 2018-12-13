import mock
import pytest

import migrate_config


def test_acquire_lock():
    old_lock = migrate_config.LOCK_FILE

    try:
        migrate_config.LOCK_FILE = '/tmp/test-acquire-lock.lock'
        # first attempt should succeed
        with migrate_config.acquire_lock():
            # second attempt should fail
            with pytest.raises(SystemExit):
                with migrate_config.acquire_lock():
                    pass
    finally:
        migrate_config.LOCK_FILE = old_lock
