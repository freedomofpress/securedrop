import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from os.path import abspath, dirname, expanduser, join, realpath
from pathlib import Path
from typing import Generator, Optional

import tbselenium.common as cm
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.remote_connection import LOGGER
from tbselenium.tbdriver import TorBrowserDriver

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


def _create_torbrowser_driver(
    accept_languages: Optional[str] = None,
) -> TorBrowserDriver:
    logging.info("Creating TorBrowserDriver")
    log_file = open(_LOGFILE_PATH, "a")
    log_file.write(f"\n\n[{datetime.now()}] Running Functional Tests\n")
    log_file.flush()

    # Don't use Tor when reading from localhost, and turn off private
    # browsing. We need to turn off private browsing because we won't be
    # able to access the browser's cookies in private browsing mode. Since
    # we use session cookies in SD anyway (in private browsing mode all
    # cookies are set as session cookies), this should not affect session
    # lifetime.
    pref_dict = {
        "network.proxy.no_proxies_on": "127.0.0.1",
        "browser.privatebrowsing.autostart": False,
    }
    if accept_languages is not None:
        pref_dict["intl.accept_languages"] = accept_languages

    Path(_TBB_PATH).mkdir(parents=True, exist_ok=True)
    torbrowser_driver = None
    for i in range(_DRIVER_RETRY_COUNT):
        try:
            torbrowser_driver = TorBrowserDriver(
                _TBB_PATH,
                tor_cfg=cm.USE_RUNNING_TOR,
                pref_dict=pref_dict,
                tbb_logfile_path=_LOGFILE_PATH,
            )
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

    return torbrowser_driver


def _create_firefox_driver(
    accept_languages: Optional[str] = None,
) -> webdriver.Firefox:
    logging.info("Creating Firefox web driver")

    profile = webdriver.FirefoxProfile()
    if accept_languages is not None:
        profile.set_preference("intl.accept_languages", accept_languages)
        profile.update_preferences()

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.binary_location = _FIREFOX_PATH
    firefox_options.profile = profile

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

    # Add this attribute to the returned driver object so that tests using this
    # fixture can know what locale it's parameterized with.
    firefox_driver.locale = accept_languages or "en_US"  # type: ignore[attr-defined]

    return firefox_driver


@contextmanager
def get_web_driver(
    web_driver_type: WebDriverTypeEnum = WebDriverTypeEnum.TOR_BROWSER,
    accept_languages: Optional[str] = None,
) -> Generator[WebDriver, None, None]:
    if web_driver_type == WebDriverTypeEnum.TOR_BROWSER:
        web_driver = _create_torbrowser_driver(accept_languages=accept_languages)
    elif web_driver_type == WebDriverTypeEnum.FIREFOX:
        web_driver = _create_firefox_driver(accept_languages=accept_languages)
    else:
        raise ValueError(f"Unexpected value {web_driver_type}")

    try:
        yield web_driver
    finally:
        try:
            web_driver.quit()
        except Exception:
            logging.exception("Error stopping driver")
