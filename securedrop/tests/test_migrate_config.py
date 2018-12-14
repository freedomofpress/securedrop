import json
import mock
import pytest

from os import path

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


def test_migrate_empty_case(tmpdir):
    '''
    The migration should not break even if the config
    '''
    config_dir = str(tmpdir)

    # dummy class with none of the `config.py` attributes
    class Dummy():

        pass

    dummy = Dummy()

    with mock.patch("migrate_config.import_config",
                    return_value=dummy) as mock_import:
        migrate_config.do_migration(True, config_dir)

    assert mock_import.called_once_with()

    journalist_json = path.join(config_dir, 'journalist-config.json')
    source_json = path.join(config_dir, 'source-config.json')

    for config_file in [journalist_json, source_json]:
        with open(config_file) as f:
            json_config = json.loads(f.read())
            assert json_config  # TODO
