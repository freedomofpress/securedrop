import json
import mock
import pytest

from os import path

import populate_config


def test_acquire_lock():
    old_lock = populate_config.LOCK_FILE

    try:
        populate_config.LOCK_FILE = '/tmp/test-acquire-lock.lock'
        # first attempt should succeed
        with populate_config.acquire_lock():
            # second attempt should fail
            with pytest.raises(SystemExit):
                with populate_config.acquire_lock():
                    pass
    finally:
        populate_config.LOCK_FILE = old_lock


def test_migrate_empty_case(tmpdir):
    '''
    The migration should not break even if the config
    '''
    config_dir = str(tmpdir)

    # dummy class with none of the `config.py` attributes
    class Dummy():

        pass

    dummy = Dummy()

    with mock.patch("populate_config.import_config",
                    return_value=dummy) as mock_import:
        populate_config.do_migration(True, config_dir)

    assert mock_import.called_once_with()

    journalist_json = path.join(config_dir, 'journalist-config.json')
    source_json = path.join(config_dir, 'source-config.json')

    for config_file in [journalist_json, source_json]:
        with open(config_file) as f:
            json_config = json.loads(f.read())
            assert json_config  # TODO
