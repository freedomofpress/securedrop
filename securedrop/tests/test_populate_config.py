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

    key_fpr = 'abc123'
    default_locale = 'de_DE'
    supported_locales = ['en_US', 'de_DE']

    with mock.patch("populate_config.import_config",
                    return_value=dummy) as mock_import:
        populate_config.migrate_and_populate_configs(
            key_fpr, default_locale, supported_locales, config_dir)

    assert mock_import.called_once_with()

    journalist_json = path.join(config_dir, 'journalist-config.json')
    source_json = path.join(config_dir, 'source-config.json')

    for config_file in [journalist_json, source_json]:
        with open(config_file) as f:
            json_config = json.loads(f.read())

            # check that secret generation succeeded
            assert len(json_config['scrypt_id_pepper']) >= 32
            assert len(json_config['scrypt_id_pepper']) >= 32
            assert len(json_config['secret_key']) >= 32

            # check that CLI args were set
            assert json_config['i18n']['default_locale'] == default_locale
            assert json_config['i18n']['supported_locales'] == \
                supported_locales


def test_migration_idempotence(tmpdir):
    config_dir = str(tmpdir)

    # dummy class with none of the `config.py` attributes
    class Dummy():

        pass

    dummy = Dummy()

    journalist_file = path.join(config_dir, 'journalist-config.json')
    source_file = path.join(config_dir, 'source-config.json')

    def migrate_and_read_files():
        with mock.patch("populate_config.import_config",
                        return_value=dummy):
            populate_config.migrate_and_populate_configs(
                None, None, None, config_dir)

        with open(journalist_file) as f:
            j_data = json.loads(f.read())

        with open(source_file) as f:
            s_data = json.loads(f.read())

        return (j_data, s_data)

    journo_conf, source_conf = migrate_and_read_files()
    new_journo_conf, new_source_conf = migrate_and_read_files()

    assert new_journo_conf == journo_conf
    assert new_source_conf == source_conf


def test_migration_no_config_py(tmpdir):
    config_dir = str(tmpdir)

    key_fpr = 'abc123'
    default_locale = 'de_DE'
    supported_locales = ['en_US', 'de_DE']

    # return None to simulate an `ImportError` within the function
    with mock.patch("populate_config.import_config",
                    return_value=None):
        populate_config.migrate_and_populate_configs(
            key_fpr, default_locale, supported_locales, config_dir)

    journalist_json = path.join(config_dir, 'journalist-config.json')
    source_json = path.join(config_dir, 'source-config.json')

    for config_file in [journalist_json, source_json]:
        with open(config_file) as f:
            json_config = json.loads(f.read())

            # check that secret generation succeeded
            assert len(json_config['scrypt_id_pepper']) >= 32
            assert len(json_config['scrypt_id_pepper']) >= 32
            assert len(json_config['secret_key']) >= 32

            # check that CLI args were set
            assert json_config['i18n']['default_locale'] == default_locale
            assert json_config['i18n']['supported_locales'] == \
                supported_locales
