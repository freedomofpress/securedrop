# -*- coding: utf-8 -*-

import argparse
import datetime
import io
import logging
import os
import time

import manage
import mock
from management import submissions
from models import Journalist, db

from .utils import db_helper


os.environ['SECUREDROP_ENV'] = 'test'  # noqa

YUBIKEY_HOTP = ['cb a0 5f ad 41 a2 ff 4e eb 53 56 3a 1b f7 23 2e ce fc dc',
                'cb a0 5f ad 41 a2 ff 4e eb 53 56 3a 1b f7 23 2e ce fc dc d7']


def test_parse_args():
    # just test that the arg parser is stable
    manage.get_args()


def test_not_verbose(caplog):
    args = manage.get_args().parse_args(['run'])
    manage.setup_verbosity(args)
    manage.log.debug('INVISIBLE')
    assert 'INVISIBLE' not in caplog.text


def test_verbose(caplog):
    args = manage.get_args().parse_args(['--verbose', 'run'])
    manage.setup_verbosity(args)
    manage.log.debug('VISIBLE')
    assert 'VISIBLE' in caplog.text


def test_get_username_success():
    with mock.patch("manage.obtain_input", return_value='jen'):
        assert manage._get_username() == 'jen'


def test_get_username_fail():
    bad_username = 'a' * (Journalist.MIN_USERNAME_LEN - 1)
    with mock.patch("manage.obtain_input",
                    side_effect=[bad_username, 'jen']):
        assert manage._get_username() == 'jen'


def test_get_yubikey_usage_yes():
    with mock.patch("manage.obtain_input", return_value='y'):
        assert manage._get_yubikey_usage()


def test_get_yubikey_usage_no():
    with mock.patch("manage.obtain_input", return_value='n'):
        assert not manage._get_yubikey_usage()


# Note: we use the `journalist_app` fixture because it creates the DB
def test_handle_invalid_secret(journalist_app, config, mocker, capsys):
    """Regression test for bad secret logic in manage.py"""

    mocker.patch("manage._get_username", return_value='ntoll'),
    mocker.patch("manage._get_first_name", return_value=''),
    mocker.patch("manage._get_last_name", return_value=''),
    mocker.patch("manage._get_yubikey_usage", return_value=True),
    mocker.patch("manage.obtain_input", side_effect=YUBIKEY_HOTP),

    with journalist_app.app_context() as context:
        # We will try to provide one invalid and one valid secret
        return_value = manage._add_user(context=context)
        out, err = capsys.readouterr()

        assert return_value == 0
        assert 'Try again.' in out
        assert 'successfully added' in out


# Note: we use the `journalist_app` fixture because it creates the DB
def test_exception_handling_when_duplicate_username(journalist_app,
                                                    config,
                                                    mocker, capsys):
    """Regression test for duplicate username logic in manage.py"""

    mocker.patch("manage._get_username", return_value='foo-bar-baz')
    mocker.patch("manage._get_first_name", return_value='')
    mocker.patch("manage._get_last_name", return_value='')
    mocker.patch("manage._get_yubikey_usage", return_value=False)

    with journalist_app.app_context() as context:
        # Inserting the user for the first time should succeed
        return_value = manage._add_user(context=context)
        out, err = capsys.readouterr()

        assert return_value == 0
        assert 'successfully added' in out

        # Inserting the user for a second time should fail
        return_value = manage._add_user()
        out, err = capsys.readouterr()
        assert return_value == 1
        assert 'ERROR: That username is already taken!' in out


# Note: we use the `journalist_app` fixture because it creates the DB
def test_delete_user(journalist_app, config, mocker):
    mocker.patch("manage._get_username", return_value='test-user-56789')
    mocker.patch("manage._get_first_name", return_value='')
    mocker.patch("manage._get_last_name", return_value='')
    mocker.patch("manage._get_yubikey_usage", return_value=False)
    mocker.patch("manage._get_username_to_delete",
                 return_value='test-user-56789')
    mocker.patch('manage._get_delete_confirmation', return_value=True)

    with journalist_app.app_context() as context:
        return_value = manage._add_user(context=context)
        assert return_value == 0

        return_value = manage.delete_user(args=None)
        assert return_value == 0


# Note: we use the `journalist_app` fixture because it creates the DB
def test_delete_non_existent_user(journalist_app, config, mocker, capsys):
    mocker.patch("manage._get_username_to_delete",
                 return_value='does-not-exist')
    mocker.patch('manage._get_delete_confirmation', return_value=True)

    with journalist_app.app_context() as context:
        return_value = manage.delete_user(args=None, context=context)
        out, err = capsys.readouterr()
        assert return_value == 0
        assert 'ERROR: That user was not found!' in out


def test_get_username_to_delete(mocker):
    mocker.patch("manage.obtain_input", return_value='test-user-12345')
    return_value = manage._get_username_to_delete()
    assert return_value == 'test-user-12345'


def test_reset(journalist_app, test_journo, alembic_config, config):
    original_config = manage.config
    try:
        # We need to override the config to point at the per-test DB
        manage.config = config
        with journalist_app.app_context() as context:
            # Override the hardcoded alembic.ini value
            manage.config.TEST_ALEMBIC_INI = alembic_config

            args = argparse.Namespace(store_dir=config.STORE_DIR)
            return_value = manage.reset(args=args, context=context)

            assert return_value == 0
            assert os.path.exists(config.DATABASE_FILE)
            assert os.path.exists(config.STORE_DIR)

            # Verify journalist user present in the database is gone
            res = Journalist.query.filter_by(username=test_journo['username']).one_or_none()
            assert res is None
    finally:
        manage.config = original_config


def test_get_username(mocker):
    mocker.patch("manage.obtain_input", return_value='foo-bar-baz')
    assert manage._get_username() == 'foo-bar-baz'


def test_get_first_name(mocker):
    mocker.patch("manage.obtain_input", return_value='foo-bar-baz')
    assert manage._get_first_name() == 'foo-bar-baz'


def test_get_last_name(mocker):
    mocker.patch("manage.obtain_input", return_value='foo-bar-baz')
    assert manage._get_last_name() == 'foo-bar-baz'


def test_clean_tmp_do_nothing(caplog):
    args = argparse.Namespace(days=0,
                              directory=' UNLIKELY::::::::::::::::: ',
                              verbose=logging.DEBUG)
    manage.setup_verbosity(args)
    manage.clean_tmp(args)
    assert 'does not exist, do nothing' in caplog.text


def test_clean_tmp_too_young(config, caplog):
    args = argparse.Namespace(days=24*60*60,
                              directory=config.TEMP_DIR,
                              verbose=logging.DEBUG)
    # create a file
    io.open(os.path.join(config.TEMP_DIR, 'FILE'), 'a').close()

    manage.setup_verbosity(args)
    manage.clean_tmp(args)
    assert 'modified less than' in caplog.text


def test_clean_tmp_removed(config, caplog):
    args = argparse.Namespace(days=0,
                              directory=config.TEMP_DIR,
                              verbose=logging.DEBUG)
    fname = os.path.join(config.TEMP_DIR, 'FILE')
    with io.open(fname, 'a'):
        old = time.time() - 24*60*60
        os.utime(fname, (old, old))
    manage.setup_verbosity(args)
    manage.clean_tmp(args)
    assert 'FILE removed' in caplog.text


def test_were_there_submissions_today(source_app, config):
    with source_app.app_context() as context:
        # We need to override the config to point at the per-test DB
        data_root = config.SECUREDROP_DATA_ROOT
        args = argparse.Namespace(data_root=data_root, verbose=logging.DEBUG)

        count_file = os.path.join(data_root, 'submissions_today.txt')
        source, codename = db_helper.init_source_without_keypair()
        source.last_updated = (datetime.datetime.utcnow() - datetime.timedelta(hours=24*2))
        db.session.commit()
        submissions.were_there_submissions_today(args, context)
        assert io.open(count_file).read() == "0"
        source.last_updated = datetime.datetime.utcnow()
        db.session.commit()
        submissions.were_there_submissions_today(args, context)
        assert io.open(count_file).read() == "1"
