import multiprocessing
import socket
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Generator, Optional, Tuple
from uuid import uuid4

import pytest
import requests
from models import Journalist
from selenium.webdriver.firefox.webdriver import WebDriver
from source_user import SourceUser
from tests.functional.db_session import get_database_session
from tests.functional.factories import SecureDropConfigFactory
from tests.functional.sd_config_v2 import SecureDropConfig
from tests.functional.web_drivers import WebDriverTypeEnum, get_web_driver


# Function-scoped so that tests can be run in parallel if needed
@pytest.fixture(scope="function")
def firefox_web_driver() -> WebDriver:
    with get_web_driver(web_driver_type=WebDriverTypeEnum.FIREFOX) as web_driver:
        yield web_driver


# Function-scoped so that tests can be run in parallel if needed
@pytest.fixture(scope="function")
def tor_browser_web_driver() -> WebDriver:
    with get_web_driver(web_driver_type=WebDriverTypeEnum.TOR_BROWSER) as web_driver:
        yield web_driver


def _get_unused_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start_source_server(port: int, config_to_use: SecureDropConfig) -> None:
    # This function will be called in a separate Process that runs the source app
    # Modify the sdconfig module in the app's memory so that it mirrors the supplied config
    # Do this BEFORE importing any other module of the application so the modified config is
    # what eventually gets imported by the app's code
    import sdconfig

    sdconfig.config = config_to_use  # type: ignore

    # Then start the source app
    from source_app import create_app

    source_app = create_app(config_to_use)  # type: ignore
    source_app.run(port=port, debug=True, use_reloader=False, threaded=True)


def _start_journalist_server(
    port: int,
    config_to_use: SecureDropConfig,
    journalist_app_setup_callback: Optional[Callable[[SecureDropConfig], None]],
) -> None:
    # This function will be called in a separate Process that runs the journalist app
    # Modify the sdconfig module in the app's memory so that it mirrors the supplied config
    # Do this BEFORE importing any other module of the application so the modified config is
    # what eventually gets imported by the app's code
    import sdconfig

    sdconfig.config = config_to_use  # type: ignore

    # Then start the journalist app
    from journalist_app import create_app

    # Some tests require a specific state to be set (such as having a submission)
    if journalist_app_setup_callback:
        journalist_app_setup_callback(config_to_use)

    journalist_app = create_app(config_to_use)  # type: ignore
    journalist_app.run(port=port, debug=True, use_reloader=False, threaded=True)


@dataclass(frozen=True)
class SdServersFixtureResult:
    source_app_base_url: str
    journalist_app_base_url: str

    # The config that's being used by the source app and journalist app
    config_in_use: SecureDropConfig

    # Credentials to log into the journalist app as a journalist/admin
    journalist_username: str
    journalist_password: str
    journalist_otp_secret: str
    journalist_is_admin: bool


@contextmanager
def spawn_sd_servers(
    config_to_use: SecureDropConfig,
    journalist_app_setup_callback: Optional[Callable[[SecureDropConfig], Any]] = None,
) -> Generator[SdServersFixtureResult, None, None]:
    """Spawn the source and journalist apps as separate processes with the supplied config.

    The journalist_app_setup_callback can be used to run a setup function within the journalist
    app's process right before the app starts (for setting up state needed by the test).
    """
    journalist_app_process = None
    source_app_process = None
    try:
        # Add a test journalist
        with get_database_session(
            database_uri=config_to_use.DATABASE_URI
        ) as db_session_for_sd_servers:
            journalist_password = "correct horse battery staple profanity oil chewy"
            journalist_username = "journalist"
            journalist_otp_secret = "JHCOGO7VCER3EJ4L"
            journalist_is_admin = True
            journalist = Journalist(
                username=journalist_username,
                password=journalist_password,
                is_admin=journalist_is_admin,
            )
            journalist.otp_secret = journalist_otp_secret
            db_session_for_sd_servers.add(journalist)
            db_session_for_sd_servers.commit()

        # Spawn the source and journalist web apps in separate processes
        source_port = _get_unused_port()
        journalist_port = _get_unused_port()

        # Start the server subprocesses using the "spawn" method instead of "fork".
        # This is needed for the config_to_use argument to work; if "fork" is used, the subprocess
        # will inherit all the globals from the parent process, which will include the Python
        # variables declared as "global" in the SD code base
        # (example: see _DesignationGenerator.get_default()).
        # This means the config_to_use will be ignored if these globals have already been
        # initialized (for example by tests running before the code here).
        mp_spawn_ctx = multiprocessing.get_context("spawn")

        source_app_process = mp_spawn_ctx.Process(  # type: ignore
            target=_start_source_server, args=(source_port, config_to_use)
        )
        source_app_process.start()
        journalist_app_process = mp_spawn_ctx.Process(  # type: ignore
            target=_start_journalist_server,
            args=(journalist_port, config_to_use, journalist_app_setup_callback),
        )
        journalist_app_process.start()
        source_app_base_url = f"http://127.0.0.1:{source_port}"
        journalist_app_base_url = f"http://127.0.0.1:{journalist_port}"

        # Sleep until the source and journalist web apps are up and running
        response_source_status_code = None
        response_journalist_status_code = None
        for _ in range(30):
            try:
                response_source = requests.get(source_app_base_url, timeout=1)
                response_source_status_code = response_source.status_code
                response_journalist = requests.get(journalist_app_base_url, timeout=1)
                response_journalist_status_code = response_journalist.status_code
                break
            except (requests.ConnectionError, requests.Timeout):
                time.sleep(0.25)
        assert response_source_status_code == 200
        assert response_journalist_status_code == 200

        # Ready for the tests
        yield SdServersFixtureResult(
            source_app_base_url=source_app_base_url,
            journalist_app_base_url=journalist_app_base_url,
            config_in_use=config_to_use,
            journalist_username=journalist_username,
            journalist_password=journalist_password,
            journalist_otp_secret=journalist_otp_secret,
            journalist_is_admin=journalist_is_admin,
        )

    # Clean everything up
    finally:
        if source_app_process:
            source_app_process.terminate()
            source_app_process.join()
        if journalist_app_process:
            journalist_app_process.terminate()
            journalist_app_process.join()


@pytest.fixture(scope="session")
def sd_servers(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SdServersFixtureResult, None, None]:
    """Spawn the source and journalist apps as separate processes with a default config.

    This fixture is session-scoped so the apps are only spawned once during the test session, and
    shared between the different unit tests. If your test needs to modify the state of the apps
    (example: a source submits a message), use the sd_servers_with_clean_state fixture, which is
    slower.
    """
    default_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path("/tmp/sd-tests/functional"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(default_config.GPG_KEY_DIR) == gpg_dir
    assert default_config.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes
    with spawn_sd_servers(config_to_use=default_config) as sd_servers_result:
        yield sd_servers_result


@pytest.fixture(scope="function")
def sd_servers_with_clean_state(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SdServersFixtureResult, None, None]:
    """Same as sd_servers but spawns the apps with a clean state.

    Slower than sd_servers as it is function-scoped.
    """
    default_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/functional-clean-state-{uuid4()}"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(default_config.GPG_KEY_DIR) == gpg_dir
    assert default_config.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes
    with spawn_sd_servers(config_to_use=default_config) as sd_servers_result:
        yield sd_servers_result


@pytest.fixture(scope="function")
def sd_servers_with_submitted_file(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SdServersFixtureResult, None, None]:
    """Same as sd_servers but spawns the apps with an already-submitted source file.

    Slower than sd_servers as it is function-scoped.
    """
    default_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/functional-with-submitted-file-{uuid4()}"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(default_config.GPG_KEY_DIR) == gpg_dir
    assert default_config.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes with a callback to create a submission
    with spawn_sd_servers(
        config_to_use=default_config, journalist_app_setup_callback=create_source_and_submission
    ) as sd_servers_result:
        yield sd_servers_result


def create_source_and_submission(config_in_use: SecureDropConfig) -> Tuple[SourceUser, Path]:
    """Directly create a source and a submission within the app.

    Some tests for the journalist app require a submission to already be present, and this
    function is used to create the source user and submission when the journalist app starts.

    This implementation is much faster than using Selenium to navigate the source app in order
    to create a submission: it takes 0.2s to run, while the Selenium implementation takes 7s.
    """
    # This function will be called in a separate Process that runs the app
    # Hence the late imports
    from encryption import EncryptionManager
    from models import Submission
    from passphrases import PassphraseGenerator
    from source_user import create_source_user
    from store import Storage, add_checksum_for_file
    from tests.functional.db_session import get_database_session

    # Create a source
    passphrase = PassphraseGenerator.get_default().generate_passphrase()
    with get_database_session(database_uri=config_in_use.DATABASE_URI) as db_session:
        source_user = create_source_user(
            db_session=db_session,
            source_passphrase=passphrase,
            source_app_storage=Storage.get_default(),
        )
        source_db_record = source_user.get_db_record()
        EncryptionManager.get_default().generate_source_key_pair(source_user)

        # Create a file submission from this source
        source_db_record.interaction_count += 1
        app_storage = Storage.get_default()
        encrypted_file_name = app_storage.save_file_submission(
            filesystem_id=source_user.filesystem_id,
            count=source_db_record.interaction_count,
            journalist_filename=source_db_record.journalist_filename,
            filename="filename.txt",
            stream=BytesIO(b"File with S3cr3t content"),
        )
        submission = Submission(source_db_record, encrypted_file_name, app_storage)
        db_session.add(submission)
        source_db_record.pending = False
        source_db_record.last_updated = datetime.now(timezone.utc)
        db_session.commit()

        submission_file_path = app_storage.path(source_user.filesystem_id, submission.filename)
        add_checksum_for_file(
            session=db_session,
            db_obj=submission,
            file_path=submission_file_path,
        )

        return source_user, Path(submission_file_path)
