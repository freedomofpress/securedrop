import configparser
import json
import logging
import os
import shutil
import signal
import subprocess
from os import path
from pathlib import Path
from typing import Any, Dict, Generator, Tuple
from unittest import mock
from uuid import uuid4

import pretty_bad_protocol as gnupg
import psutil
import pytest
import sdconfig
from db import db
from flask import Flask, url_for
from journalist_app import create_app as create_journalist_app
from passphrases import PassphraseGenerator
from sdconfig import DEFAULT_SECUREDROP_ROOT, SecureDropConfig
from source_app import create_app as create_source_app
from source_user import _SourceScryptManager, create_source_user
from store import Storage
from tests import utils
from tests.factories import SecureDropConfigFactory
from tests.utils import i18n
from two_factor import TOTP

# Quiet down gnupg output. (See Issue #2595)
GNUPG_LOG_LEVEL = os.environ.get("GNUPG_LOG_LEVEL", "ERROR")
gnupg._util.log.setLevel(getattr(logging, GNUPG_LOG_LEVEL, logging.ERROR))


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
        # TODO: we don't need the journalist pub key in the keyring anymore, but include
        # it anyways to match a legacy prod keyring.
        journalist_key_fingerprint = gpg.import_keys(journalist_public_key).fingerprints[0]

        yield journalist_key_fingerprint, tmp_gpg_dir

    finally:
        shutil.rmtree(tmp_gpg_dir, ignore_errors=True)


@pytest.fixture
def config(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path],
    setup_rqworker: Tuple[str, str],
) -> Generator[SecureDropConfig, None, None]:
    journalist_key_fingerprint, gpg_key_dir = setup_journalist_key_and_gpg_folder
    worker_name, _ = setup_rqworker
    config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/conftest-{uuid4()}"),
        GPG_KEY_DIR=gpg_key_dir,
        JOURNALIST_KEY=journalist_key_fingerprint,
        SUPPORTED_LOCALES=i18n.get_test_locales(),
        RQ_WORKER_NAME=worker_name,
    )

    # Set this newly-created config as the current config
    with mock.patch.object(sdconfig.SecureDropConfig, "get_current", return_value=config):
        yield config


@pytest.fixture
def alembic_config(config: SecureDropConfig) -> Generator[Path, None, None]:
    base_dir = path.join(path.dirname(__file__), "..")
    migrations_dir = path.join(base_dir, "alembic")
    ini = configparser.ConfigParser()
    ini.read(path.join(base_dir, "alembic.ini"))

    ini.set("alembic", "script_location", path.join(migrations_dir))
    ini.set("alembic", "sqlalchemy.url", config.DATABASE_URI)

    alembic_path = config.SECUREDROP_DATA_ROOT / "alembic.ini"
    with open(alembic_path, "w") as f:
        ini.write(f)

    # The alembic tests require the SECUREDROP_ENV env variable to be set to "test"
    # because alembic migrations are run in a separate process that reads
    # the config.py separately; hence the config fixture doesn't get applied
    # and without this, the alembic process will use the "prod" value of
    # SECUREDROP_DATA_ROOT that is defined in the config.py.example
    previous_env_value = os.getenv("SECUREDROP_ENV", default="")
    os.environ["SECUREDROP_ENV"] = "test"

    try:
        yield alembic_path

    finally:
        os.environ["SECUREDROP_ENV"] = previous_env_value


@pytest.fixture
def app_storage(config: SecureDropConfig) -> "Storage":
    return Storage(str(config.STORE_DIR), str(config.TEMP_DIR))


@pytest.fixture
def source_app(config: SecureDropConfig, app_storage: Storage) -> Generator[Flask, None, None]:
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


@pytest.fixture
def journalist_app(config: SecureDropConfig, app_storage: Storage) -> Generator[Flask, None, None]:
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def test_source(journalist_app: Flask, app_storage: Storage) -> Dict[str, Any]:
    with journalist_app.app_context():
        passphrase = PassphraseGenerator.get_default().generate_passphrase()
        source_user = create_source_user(
            db_session=db.session,
            source_passphrase=passphrase,
            source_app_storage=app_storage,
        )
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture(scope="session")
def setup_rqworker() -> Generator[Tuple[str, Path], None, None]:
    # The PID file and name for the redis worker are hard-coded below
    test_worker_pid_file = Path("/tmp/securedrop_test_worker.pid")
    test_worker_name = "test"

    try:
        _start_test_rqworker(
            worker_name=test_worker_name,
            worker_pid_file=test_worker_pid_file,
            securedrop_root=DEFAULT_SECUREDROP_ROOT,
        )

        yield test_worker_name, test_worker_pid_file

    finally:
        _stop_test_rqworker(test_worker_pid_file)


def _start_test_rqworker(worker_name: str, worker_pid_file: Path, securedrop_root: Path) -> None:
    if not psutil.pid_exists(_get_pid_from_file(worker_pid_file)):
        tmp_logfile = open("/tmp/test_rqworker.log", "w")
        subprocess.Popen(
            [
                "rqworker",
                worker_name,
                "-P",
                securedrop_root,
                "-c",
                "rq_config",
                "--pid",
                worker_pid_file,
                "--logging_level",
                "DEBUG",
                "-v",
            ],
            stdout=tmp_logfile,
            stderr=subprocess.STDOUT,
        )


def _stop_test_rqworker(worker_pid_file: Path) -> None:
    rqworker_pid = _get_pid_from_file(worker_pid_file)
    if rqworker_pid:
        os.kill(rqworker_pid, signal.SIGTERM)
        try:
            os.remove(worker_pid_file)
        except OSError:
            pass


def _get_pid_from_file(pid_file_name: Path) -> int:
    try:
        return int(open(pid_file_name).read())
    except OSError:
        return -1
