# -*- coding: utf-8 -*-

import configparser
import json
import logging
import os
import shutil
import signal
import subprocess
from os import path
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Generator, Tuple
from unittest import mock
from unittest.mock import PropertyMock

import models
import pretty_bad_protocol as gnupg
import psutil
import pytest
import sdconfig
from db import db
from encryption import EncryptionManager
from flask import Flask, url_for
from hypothesis import settings
from journalist_app import create_app as create_journalist_app
from passphrases import PassphraseGenerator
from pyotp import TOTP
from sdconfig import SDConfig
from sdconfig import config as original_config
from source_app import create_app as create_source_app
from source_user import _SourceScryptManager, create_source_user
from store import Storage

from . import utils
from .utils import i18n

# The PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
TEST_WORKER_PIDFILE = "/tmp/securedrop_test_worker.pid"

# Quiet down gnupg output. (See Issue #2595)
GNUPG_LOG_LEVEL = os.environ.get("GNUPG_LOG_LEVEL", "ERROR")
gnupg._util.log.setLevel(getattr(logging, GNUPG_LOG_LEVEL, logging.ERROR))

# `hypothesis` sets a default deadline of 200 milliseconds before failing tests,
# which doesn't work for integration tests. Turn off deadlines.
settings.register_profile("securedrop", deadline=None)
settings.load_profile("securedrop")


def pytest_addoption(parser):
    parser.addoption(
        "--page-layout", action="store_true", default=False, help="run page layout tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "pagelayout: Tests which verify page layout")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--page-layout"):
        return
    skip_page_layout = pytest.mark.skip(reason="need --page-layout option to run page layout tests")
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


@pytest.fixture(scope="session")
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
        scrypt_n=2**1,
        scrypt_r=1,
        scrypt_p=1,
    )

    with mock.patch.object(_SourceScryptManager, "get_default", return_value=insecure_scrypt_mgr):
        yield


@pytest.fixture(scope="session")
def setup_journalist_key_and_gpg_folder() -> Generator[Tuple[str, Path], None, None]:
    """Set up the journalist test key and the key folder, and reduce source key length for speed.

    This fixture takes about 2s to complete hence we use the "session" scope to only run it once.
    """
    # This path matches the GPG_KEY_DIR defined in the config.py used for the tests
    # If they don't match, it can make the tests flaky and very hard to debug
    tmp_gpg_dir = Path("/tmp") / "securedrop" / "keys"
    tmp_gpg_dir.mkdir(parents=True, exist_ok=True, mode=0o0700)

    try:
        # GPG 2.1+ requires gpg-agent, see #4013
        gpg_agent_config = tmp_gpg_dir / "gpg-agent.conf"
        gpg_agent_config.write_text("allow-loopback-pinentry\ndefault-cache-ttl 0")

        # Import the journalist public key in GPG
        # WARNING: don't import the journalist secret key; it will make the decryption tests
        # unreliable
        gpg = gnupg.GPG("gpg2", homedir=str(tmp_gpg_dir))
        journalist_public_key_path = Path(__file__).parent / "files" / "test_journalist_key.pub"
        journalist_public_key = journalist_public_key_path.read_text()
        journalist_key_fingerprint = gpg.import_keys(journalist_public_key).fingerprints[0]

        # Reduce source GPG key length to speed up tests at the expense of security
        with mock.patch.object(
            EncryptionManager, "GPG_KEY_LENGTH", PropertyMock(return_value=1024)
        ):

            yield journalist_key_fingerprint, tmp_gpg_dir

    finally:
        shutil.rmtree(tmp_gpg_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def config(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SDConfig, None, None]:
    config = SDConfig()
    journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
    config.GPG_KEY_DIR = str(gpg_key_dir)
    config.JOURNALIST_KEY = journalist_key_fingerprint

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

        # Set this newly-created config as the "global" config
        with mock.patch.object(sdconfig, "config", config):

            yield config


@pytest.fixture(scope="function")
def alembic_config(config: SDConfig) -> str:
    base_dir = path.join(path.dirname(__file__), "..")
    migrations_dir = path.join(base_dir, "alembic")
    ini = configparser.ConfigParser()
    ini.read(path.join(base_dir, "alembic.ini"))

    ini.set("alembic", "script_location", path.join(migrations_dir))
    ini.set("alembic", "sqlalchemy.url", config.DATABASE_URI)

    alembic_path = path.join(config.SECUREDROP_DATA_ROOT, "alembic.ini")
    with open(alembic_path, "w") as f:
        ini.write(f)

    return alembic_path


@pytest.fixture(scope="function")
def app_storage(config: SDConfig) -> "Storage":
    return Storage(config.STORE_DIR, config.TEMP_DIR)


@pytest.fixture(scope="function")
def source_app(config: SDConfig, app_storage: Storage) -> Generator[Flask, None, None]:
    config.SOURCE_APP_FLASK_CONFIG_CLS.TESTING = True
    config.SOURCE_APP_FLASK_CONFIG_CLS.USE_X_SENDFILE = False

    # Disable CSRF checks to make writing tests easier
    config.SOURCE_APP_FLASK_CONFIG_CLS.WTF_CSRF_ENABLED = False

    with mock.patch("store.Storage.get_default") as mock_storage_global:
        mock_storage_global.return_value = app_storage
        app = create_source_app(config)
        app.config["SERVER_NAME"] = "localhost.localdomain"
        with app.app_context():
            db.create_all()
            try:
                yield app
            finally:
                db.session.rollback()
                db.drop_all()


@pytest.fixture(scope="function")
def journalist_app(config: SDConfig, app_storage: Storage) -> Generator[Flask, None, None]:
    config.JOURNALIST_APP_FLASK_CONFIG_CLS.TESTING = True
    config.JOURNALIST_APP_FLASK_CONFIG_CLS.USE_X_SENDFILE = False

    # Disable CSRF checks to make writing tests easier
    config.JOURNALIST_APP_FLASK_CONFIG_CLS.WTF_CSRF_ENABLED = False

    with mock.patch("store.Storage.get_default") as mock_storage_global:
        mock_storage_global.return_value = app_storage
        app = create_journalist_app(config)
        app.config["SERVER_NAME"] = "localhost.localdomain"
        with app.app_context():
            db.create_all()
            try:
                yield app
            finally:
                db.session.rollback()
                db.drop_all()


@pytest.fixture(scope="function")
def test_journo(journalist_app: Flask) -> Dict[str, Any]:
    with journalist_app.app_context():
        user, password = utils.db_helper.init_journalist(is_admin=False)
        username = user.username
        otp_secret = user.otp_secret
        return {
            "journalist": user,
            "username": username,
            "password": password,
            "otp_secret": otp_secret,
            "id": user.id,
            "uuid": user.uuid,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }


@pytest.fixture(scope="function")
def test_admin(journalist_app: Flask) -> Dict[str, Any]:
    with journalist_app.app_context():
        user, password = utils.db_helper.init_journalist(is_admin=True)
        username = user.username
        otp_secret = user.otp_secret
        return {
            "admin": user,
            "username": username,
            "password": password,
            "otp_secret": otp_secret,
            "id": user.id,
        }


@pytest.fixture(scope="function")
def test_source(journalist_app: Flask, app_storage: Storage) -> Dict[str, Any]:
    with journalist_app.app_context():
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_storage=app_storage,
        )
        EncryptionManager.get_default().generate_source_key_pair(source_user)
        source = source_user.get_db_record()
        return {
            "source_user": source_user,
            # TODO(AD): Eventually the next keys could be removed as they are in source_user
            "source": source,
            "codename": passphrase,
            "filesystem_id": source_user.filesystem_id,
            "uuid": source.uuid,
            "id": source.id,
        }


@pytest.fixture(scope="function")
def test_submissions(journalist_app: Flask, app_storage: Storage) -> Dict[str, Any]:
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source(app_storage)
        utils.db_helper.submit(app_storage, source, 2)
        return {
            "source": source,
            "codename": codename,
            "filesystem_id": source.filesystem_id,
            "uuid": source.uuid,
            "submissions": source.submissions,
        }


@pytest.fixture(scope="function")
def test_files(journalist_app, test_journo, app_storage):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source(app_storage)
        utils.db_helper.submit(app_storage, source, 2, submission_type="file")
        utils.db_helper.reply(app_storage, test_journo["journalist"], source, 1)
        return {
            "source": source,
            "codename": codename,
            "filesystem_id": source.filesystem_id,
            "uuid": source.uuid,
            "submissions": source.submissions,
            "replies": source.replies,
        }


@pytest.fixture(scope="function")
def test_files_deleted_journalist(journalist_app, test_journo, app_storage):
    with journalist_app.app_context():
        source, codename = utils.db_helper.init_source(app_storage)
        utils.db_helper.submit(app_storage, source, 2)
        test_journo["journalist"]
        juser, _ = utils.db_helper.init_journalist("f", "l", is_admin=False)
        utils.db_helper.reply(app_storage, juser, source, 1)
        utils.db_helper.delete_journalist(juser)
        return {
            "source": source,
            "codename": codename,
            "filesystem_id": source.filesystem_id,
            "uuid": source.uuid,
            "submissions": source.submissions,
            "replies": source.replies,
        }


@pytest.fixture(scope="function")
def journalist_api_token(journalist_app, test_journo):
    with journalist_app.test_client() as app:
        valid_token = TOTP(test_journo["otp_secret"]).now()
        response = app.post(
            url_for("api.get_token"),
            data=json.dumps(
                {
                    "username": test_journo["username"],
                    "passphrase": test_journo["password"],
                    "one_time_code": valid_token,
                }
            ),
            headers=utils.api_helper.get_api_headers(),
        )
        return response.json["token"]


def _start_test_rqworker(config: SDConfig) -> None:
    if not psutil.pid_exists(_get_pid_from_file(TEST_WORKER_PIDFILE)):
        tmp_logfile = open("/tmp/test_rqworker.log", "w")
        subprocess.Popen(
            [
                "rqworker",
                config.RQ_WORKER_NAME,
                "-P",
                config.SECUREDROP_ROOT,
                "--pid",
                TEST_WORKER_PIDFILE,
                "--logging_level",
                "DEBUG",
                "-v",
            ],
            stdout=tmp_logfile,
            stderr=subprocess.STDOUT,
        )


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
