# -*- coding: utf-8 -*-

import configparser
from pathlib import Path
from tempfile import TemporaryDirectory

from typing import Any, Generator

from unittest import mock

import pretty_bad_protocol as gnupg
import logging

from flask import Flask
from hypothesis import settings
import os
import json
import psutil
import pytest
import shutil
import signal
import subprocess

from flask import url_for
from pyotp import TOTP
from typing import Dict

# WARNING: This variable must be set before any import of the securedrop code/app
# or most tests will fail
os.environ['SECUREDROP_ENV'] = 'test'  # noqa

from passphrases import PassphraseGenerator
from source_user import _SourceScryptManager, create_source_user

from sdconfig import SDConfig, config as original_config

from os import path

from db import db
from journalist_app import create_app as create_journalist_app
import models
from source_app import create_app as create_source_app
from . import utils
from .utils import i18n

# The PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
TEST_WORKER_PIDFILE = '/tmp/securedrop_test_worker.pid'

# Quiet down gnupg output. (See Issue #2595)
GNUPG_LOG_LEVEL = os.environ.get('GNUPG_LOG_LEVEL', "ERROR")
gnupg._util.log.setLevel(getattr(logging, GNUPG_LOG_LEVEL, logging.ERROR))

# `hypothesis` sets a default deadline of 200 milliseconds before failing tests,
# which doesn't work for integration tests. Turn off deadlines.
settings.register_profile("securedrop", deadline=None)
settings.load_profile("securedrop")


def pytest_addoption(parser):
    parser.addoption("--page-layout", action="store_true",
                     default=False, help="run page layout tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--page-layout"):
        return
    skip_page_layout = pytest.mark.skip(
        reason="need --page-layout option to run page layout tests"
    )
    for item in items:
        if "pagelayout" in item.keywords:
            item.add_marker(skip_page_layout)


@pytest.fixture
def hardening(request):
    hardening = models.LOGIN_HARDENING

    def finalizer():
        models.LOGIN_HARDENING = hardening
    request.addfinalizer(finalizer)
    models.LOGIN_HARDENING = True
    return None


@pytest.fixture(scope='session')
def setUpTearDown():
    _start_test_rqworker(original_config)
    yield
    _stop_test_rqworker()
    _cleanup_test_securedrop_dataroot(original_config)


def insecure_scrypt() -> Generator[None, None, None]:
    """Make scrypt insecure but fast for the test suite."""
    insecure_scrypt_mgr = _SourceScryptManager(
        salt_for_gpg_secret=b"abcd",
        salt_for_filesystem_id=b"1234",
        # Insecure but fast
        scrypt_n=2 ** 1,
        scrypt_r=1,
        scrypt_p=1,
    )

    with mock.patch.object(_SourceScryptManager, "get_default", return_value=insecure_scrypt_mgr):
        yield


@pytest.fixture(scope="session")
def gpg_key_dir() -> Generator[Path, None, None]:
    """Set up the journalist test key in GPG and the parent folder.

    This fixture takes about 2s to complete hence we use the "session" scope to only run it once.
    """
    with TemporaryDirectory() as tmp_gpg_dir_name:
        tmp_gpg_dir = Path(tmp_gpg_dir_name)

        # GPG 2.1+ requires gpg-agent, see #4013
        gpg_agent_config = tmp_gpg_dir / "gpg-agent.conf"
        gpg_agent_config.write_text("allow-loopback-pinentry")

        # Import the test key in GPG
        gpg = gnupg.GPG("gpg2", homedir=str(tmp_gpg_dir))
        test_keys_dir = Path(__file__).parent / "files"
        for ext in ["sec", "pub"]:
            key_file = test_keys_dir / "test_journalist_key.{}".format(ext)
            gpg.import_keys(key_file.read_text())

        yield tmp_gpg_dir


@pytest.fixture(scope='function')
def config(gpg_key_dir: Path) -> Generator[SDConfig, None, None]:
    config = SDConfig()
    config.GPG_KEY_DIR = str(gpg_key_dir)

    # Setup the filesystem for the application
    with TemporaryDirectory() as data_dir_name:
        data_dir = Path(data_dir_name)
        config.SECUREDROP_DATA_ROOT = str(data_dir)

        store_dir = data_dir / "store"
        store_dir.mkdir()
        config.STORE_DIR = str(store_dir)

        tmp_dir = data_dir / "tmp"
        tmp_dir.mkdir()
        config.TEMP_DIR = str(tmp_dir)

        # Create the db file
        sqlite_db_path = data_dir / "db.sqlite"
        config.DATABASE_FILE = str(sqlite_db_path)
        subprocess.check_call(["sqlite3", config.DATABASE_FILE, ".databases"])

        config.SUPPORTED_LOCALES = i18n.get_test_locales()

        yield config


@pytest.fixture(scope='function')
def alembic_config(config: SDConfig) -> str:
    base_dir = path.join(path.dirname(__file__), '..')
    migrations_dir = path.join(base_dir, 'alembic')
    ini = configparser.ConfigParser()
    ini.read(path.join(base_dir, 'alembic.ini'))

    ini.set('alembic', 'script_location', path.join(migrations_dir))
    ini.set('alembic', 'sqlalchemy.url', config.DATABASE_URI)

    alembic_path = path.join(config.SECUREDROP_DATA_ROOT, 'alembic.ini')
    with open(alembic_path, 'w') as f:
        ini.write(f)

    return alembic_path


@pytest.fixture(scope='function')
def source_app(config: SDConfig) -> Generator[Flask, None, None]:
    app = create_source_app(config)
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.rollback()
            db.drop_all()


@pytest.fixture(scope='function')
def journalist_app(config: SDConfig) -> Generator[Flask, None, None]:
    app = create_journalist_app(config)
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.rollback()
            db.drop_all()


@pytest.fixture(scope='function')
def test_journo(journalist_app: Flask) -> Dict[str, Any]:
    with journalist_app.app_context():
        user, password = utils.db_helper.init_journalist(is_admin=False)
        username = user.username
        otp_secret = user.otp_secret
        return {'journalist': user,
                'username': username,
                'password': password,
                'otp_secret': otp_secret,
                'id': user.id,
                'uuid': user.uuid,
                'first_name': user.first_name,
                'last_name': user.last_name}


@pytest.fixture(scope='function')
def test_admin(journalist_app: Flask) -> Dict[str, Any]:
    with journalist_app.app_context():
        user, password = utils.db_helper.init_journalist(is_admin=True)
        username = user.username
        otp_secret = user.otp_secret
        return {'admin': user,
                'username': username,
                'password': password,
                'otp_secret': otp_secret,
                'id': user.id}


@pytest.fixture(scope='function')
def test_source(journalist_app: Flask) -> Dict[str, Any]:
    with journalist_app.app_context():
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_crypto_util=journalist_app.crypto_util,
            source_app_storage=journalist_app.storage,
        )
        journalist_app.crypto_util.genkeypair(source_user)
        source = source_user.get_db_record()
        return {'source_user': source_user,
                # TODO(AD): Eventually the nexy keys could be removed as they are in source_user
                'source': source,
                'codename': passphrase,
                'filesystem_id': source_user.filesystem_id,
                'uuid': source.uuid,
                'id': source.id}


@pytest.fixture(scope='function')
def test_submissions(journalist_app: Flask) -> Dict[str, Any]:
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        utils.db_helper.submit(source, 2)
        return {'source': source,
                'codename': codename,
                'filesystem_id': source.filesystem_id,
                'uuid': source.uuid,
                'submissions': source.submissions}


@pytest.fixture(scope='function')
def test_files(journalist_app, test_journo):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        utils.db_helper.submit(source, 2, submission_type="file")
        utils.db_helper.reply(test_journo['journalist'], source, 1)
        return {'source': source,
                'codename': codename,
                'filesystem_id': source.filesystem_id,
                'uuid': source.uuid,
                'submissions': source.submissions,
                'replies': source.replies}


@pytest.fixture(scope='function')
def test_files_deleted_journalist(journalist_app, test_journo):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source()
        utils.db_helper.submit(source, 2)
        test_journo['journalist']
        juser, _ = utils.db_helper.init_journalist("f", "l", is_admin=False)
        utils.db_helper.reply(juser, source, 1)
        utils.db_helper.delete_journalist(juser)
        return {'source': source,
                'codename': codename,
                'filesystem_id': source.filesystem_id,
                'uuid': source.uuid,
                'submissions': source.submissions,
                'replies': source.replies}


@pytest.fixture(scope='function')
def journalist_api_token(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo['otp_secret']).now()
        response = app.post(url_for('api.get_token'),
                            data=json.dumps(
                                {'username': test_journo['username'],
                                 'passphrase': test_journo['password'],
                                 'one_time_code': valid_token}),
                            headers=utils.api_helper.get_api_headers())
        return response.json['token']


def _start_test_rqworker(config: SDConfig) -> None:
    if not psutil.pid_exists(_get_pid_from_file(TEST_WORKER_PIDFILE)):
        tmp_logfile = open('/tmp/test_rqworker.log', 'w')
        subprocess.Popen(['rqworker', config.RQ_WORKER_NAME,
                          '-P', config.SECUREDROP_ROOT,
                          '--pid', TEST_WORKER_PIDFILE,
                          '--logging_level', 'DEBUG',
                          '-v'],
                         stdout=tmp_logfile,
                         stderr=subprocess.STDOUT)


def _stop_test_rqworker() -> None:
    rqworker_pid = _get_pid_from_file(TEST_WORKER_PIDFILE)
    if rqworker_pid:
        os.kill(rqworker_pid, signal.SIGTERM)
        try:
            os.remove(TEST_WORKER_PIDFILE)
        except OSError:
            pass


def _get_pid_from_file(pid_file_name: str) -> int:
    try:
        return int(open(pid_file_name).read())
    except IOError:
        return -1


def _cleanup_test_securedrop_dataroot(config: SDConfig) -> None:
    # Keyboard interrupts or dropping to pdb after a test failure sometimes
    # result in the temporary test SecureDrop data root not being deleted.
    try:
        shutil.rmtree(config.SECUREDROP_DATA_ROOT)
    except OSError:
        pass
