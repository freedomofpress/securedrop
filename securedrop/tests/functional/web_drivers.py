import logging
import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from os.path import abspath, dirname, expanduser, join, realpath
from pathlib import Path
from typing import Any

import tbselenium.common as cm
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.remote_connection import LOGGER
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import set_tbb_pref

_LOGFILE_PATH = abspath(join(dirname(realpath(__file__)), "../log/driver.log"))
_FIREFOX_PATH = "/usr/bin/firefox/firefox"

_TBB_PATH = abspath(expanduser("~/.local/tbb/tor-browser/"))
os.environ["TBB_PATH"] = _TBB_PATH

LOGGER.setLevel(logging.WARNING)

# width & height of the browser window. If the top of screenshot is cropped,
# increase the height of the window so the whole page fits in the window.
_BROWSER_SIZE = (1024, 1400)


class WebDriverTypeEnum(Enum):
    TOR_BROWSER = 1
    FIREFOX = 2


_DRIVER_RETRY_COUNT = 3
_DRIVER_RETRY_INTERVAL = 5


def _create_driver(
    web_driver_type: WebDriverTypeEnum, accept_languages: str | None = None, **kwargs: Any
) -> WebDriver:
    """
    Creates and configures a WebDriver instance based on the specified driver class.

    Args:
        web_driver_type: The WebDriver class to instantiate (TorBrowserDriver or Firefox)
        accept_languages: Optional language preferences string
        **kwargs: Additional keyword arguments

    Returns:
        Configured WebDriver instance

    Raises:
        ValueError: If an unsupported driver class is provided
        Exception: If driver creation fails after retry attempts
    """
    if web_driver_type not in WebDriverTypeEnum:
        raise ValueError(f"Unsupported driver class: {web_driver_type}")

    if web_driver_type == WebDriverTypeEnum.TOR_BROWSER:
        logging.info("Creating TorBrowserDriver")
        log_file = open(_LOGFILE_PATH, "a")
        log_file.write(f"\n\n[{datetime.now()}] Running Functional Tests\n")
        log_file.flush()

        pref_dict = {
            "network.proxy.no_proxies_on": "127.0.0.1",
            "browser.privatebrowsing.autostart": False,
            "remote.system-access-check.enabled": False,
        }

        Path(_TBB_PATH).mkdir(parents=True, exist_ok=True)
        torbrowser_driver = None
        for i in range(_DRIVER_RETRY_COUNT):
            try:
                tb_options = webdriver.FirefoxOptions()
                tb_options.add_argument("-remote-allow-system-access")
                torbrowser_driver = TorBrowserDriver(
                    _TBB_PATH,
                    options=tb_options,
                    tor_cfg=cm.USE_RUNNING_TOR,
                    pref_dict=pref_dict,
                    tbb_logfile_path=_LOGFILE_PATH,
                )
                if accept_languages is not None:
                    set_tbb_pref(torbrowser_driver, "privacy.spoof_english", 1)
                    set_tbb_pref(torbrowser_driver, "intl.locale.requested", accept_languages)

                logging.info("Created Tor Browser web driver")
                torbrowser_driver.set_window_position(0, 0)
                torbrowser_driver.set_window_size(*_BROWSER_SIZE)
                break
            except Exception as e:
                logging.error("Error creating Tor Browser web driver: %s", e)
                if i < _DRIVER_RETRY_COUNT:
                    time.sleep(_DRIVER_RETRY_INTERVAL)

        if not torbrowser_driver:
            raise Exception("Could not create Tor Browser web driver")

        torbrowser_driver.locale = accept_languages  # type: ignore[attr-defined]
        return torbrowser_driver

    else:  # Firefox driver
        logging.info("Creating Firefox web driver")
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.binary_location = _FIREFOX_PATH
        if accept_languages is not None:
            firefox_options.set_preference("intl.accept_languages", accept_languages)

        firefox_driver = None
        for i in range(_DRIVER_RETRY_COUNT):
            try:
                firefox_driver = webdriver.Firefox(options=firefox_options)
                firefox_driver.set_window_position(0, 0)
                firefox_driver.set_window_size(*_BROWSER_SIZE)
                logging.info("Created Firefox web driver")
                break
            except Exception as e:
                logging.error("Error creating Firefox web driver: %s", e)
                if i < _DRIVER_RETRY_COUNT:
                    time.sleep(_DRIVER_RETRY_INTERVAL)

        if not firefox_driver:
            raise Exception("Could not create Firefox web driver")

        firefox_driver.locale = accept_languages  # type: ignore[attr-defined]
        return firefox_driver


@contextmanager
def get_web_driver(
    web_driver_type: WebDriverTypeEnum,
    accept_languages: str | None = None,
) -> Generator[WebDriver, None, None]:
    # Creates the webdriver based on the class inserted
    web_driver = _create_driver(web_driver_type=web_driver_type, accept_languages=accept_languages)
    try:
        yield web_driver
    finally:
        try:
            web_driver.quit()
        except Exception:
            logging.exception("Error stopping driver")
