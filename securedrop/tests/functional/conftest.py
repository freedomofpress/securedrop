from contextlib import contextmanager
from dataclasses import dataclass
from multiprocessing.context import Process
from pathlib import Path
from typing import Generator
import requests
from selenium.webdriver.firefox.webdriver import WebDriver

import pytest
from models import Journalist
from tests.functional.db_session import get_database_session
from tests.functional.factories import SecureDropConfigFactory
from tests.functional.sd_config_v2 import SecureDropConfig
from tests.functional.web_drivers import WebDriverTypeEnum, get_web_driver
import socket
import time


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


def _start_journalist_server(port: int, config_to_use: SecureDropConfig) -> None:
    # This function will be called in a separate Process that runs the journalist app
    # Modify the sdconfig module in the app's memory so that it mirrors the supplied config
    # Do this BEFORE importing any other module of the application so the modified config is
    # what eventually gets imported by the app's code
    import sdconfig

    sdconfig.config = config_to_use  # type: ignore

    # Then start the journalist app
    from journalist_app import create_app

    journalist_app = create_app(config_to_use)  # type: ignore
    journalist_app.run(port=port, debug=True, use_reloader=False, threaded=True)


@dataclass(frozen=True)
class SdServersFixtureResult:
    source_app_base_url: str
    journalist_app_base_url: str


@contextmanager
def spawn_sd_servers(
    config_to_use: SecureDropConfig
) -> Generator[SdServersFixtureResult, None, None]:
    """Spawn the source and journalist apps as separate processes with the supplied config."""
    journalist_app_process = None
    source_app_process = None
    try:
        # Add a test journalist
        with get_database_session(
            database_uri=config_to_use.DATABASE_URI
        ) as db_session_for_sd_servers:
            journalist = Journalist(
                username="journalist",
                password="correct horse battery staple profanity oil chewy",
                is_admin=True,
            )
            journalist.otp_secret = "JHCOGO7VCER3EJ4L"
            db_session_for_sd_servers.add(journalist)
            db_session_for_sd_servers.commit()

        # Spawn the source and journalist web apps in separate processes
        source_port = _get_unused_port()
        journalist_port = _get_unused_port()
        source_app_process = Process(target=_start_source_server, args=(source_port, config_to_use))
        source_app_process.start()
        journalist_app_process = Process(
            target=_start_journalist_server, args=(journalist_port, config_to_use)
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
            except requests.ConnectionError:
                time.sleep(0.25)
        assert response_source_status_code == 200
        assert response_journalist_status_code == 200

        # Ready for the tests
        yield SdServersFixtureResult(
            source_app_base_url=source_app_base_url,
            journalist_app_base_url=journalist_app_base_url,
        )

    # Clean everything up
    finally:
        if source_app_process:
            source_app_process.terminate()
            source_app_process.join()
        if journalist_app_process:
            journalist_app_process.terminate()
            journalist_app_process.join()


# TODO(AD): This is intended to eventually replace the sd_servers fixture
@pytest.fixture(scope="session")
def sd_servers_v2(setup_journalist_key_and_gpg_folder):
    """Spawn the source and journalist apps as separate processes with a default config."""
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
