from contextlib import contextmanager
import logging
import os
from pathlib import Path
from enum import Enum
import time
from datetime import datetime
from os.path import abspath
from os.path import dirname
from os.path import expanduser
from os.path import join
from os.path import realpath
from typing import Generator, Optional

from selenium.webdriver.firefox.webdriver import WebDriver

import tbselenium.common as cm
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tbselenium.tbdriver import TorBrowserDriver


LOGFILE_PATH = abspath(join(dirname(realpath(__file__)), "../log/driver.log"))
FIREFOX_PATH = "/usr/bin/firefox/firefox"

TBB_PATH = abspath(join(expanduser("~"), ".local/tbb/tor-browser_en-US/"))
os.environ["TBB_PATH"] = TBB_PATH
TBBRC = join(TBB_PATH, "Browser/TorBrowser/Data/Tor/torrc")
LOGGER.setLevel(logging.WARNING)

# width & height of the browser window. If the top of screenshots is cropped,
# increase the height of the window so the the whole page fits in the window.
BROWSER_SIZE = (1024, 1400)


class WebDriverTypeEnum(Enum):
    TOR_BROWSER = 1
    FIREFOX = 2


_DRIVER_RETRY_COUNT = 3
_DRIVER_RETRY_INTERNVAL = 5


def _create_torbrowser_driver(
    accept_languages: Optional[str] = None,
) -> TorBrowserDriver:
    logging.info("Creating TorBrowserDriver")
    log_file = open(LOGFILE_PATH, "a")
    log_file.write("\n\n[%s] Running Functional Tests\n" % str(datetime.now()))
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

    Path(TBB_PATH).mkdir(parents=True, exist_ok=True)
    torbrowser_driver = None
    for i in range(_DRIVER_RETRY_COUNT):
        try:
            torbrowser_driver = TorBrowserDriver(
                TBB_PATH,
                tor_cfg=cm.USE_RUNNING_TOR,
                pref_dict=pref_dict,
                tbb_logfile_path=LOGFILE_PATH,
            )
            logging.info("Created Tor Browser web driver")
            torbrowser_driver.set_window_position(0, 0)
            torbrowser_driver.set_window_size(*BROWSER_SIZE)
            break
        except Exception as e:
            logging.error("Error creating Tor Browser web driver: %s", e)
            if i < _DRIVER_RETRY_COUNT:
                time.sleep(_DRIVER_RETRY_INTERNVAL)

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

    firefox_driver = None
    for i in range(_DRIVER_RETRY_COUNT):
        try:
            firefox_driver = webdriver.Firefox(firefox_binary=FIREFOX_PATH, firefox_profile=profile)
            firefox_driver.set_window_position(0, 0)
            firefox_driver.set_window_size(*BROWSER_SIZE)
            logging.info("Created Firefox web driver")
            break
        except Exception as e:
            logging.error("Error creating Firefox web driver: %s", e)
            if i < _DRIVER_RETRY_COUNT:
                time.sleep(_DRIVER_RETRY_INTERNVAL)

    if not firefox_driver:
        raise Exception("Could not create Firefox web driver")

    return firefox_driver


# TODO(AD): This could eventually replace the web driver code in FunctionalTest
@contextmanager
def get_web_driver(
    web_driver_type: WebDriverTypeEnum = WebDriverTypeEnum.TOR_BROWSER,
) -> Generator[WebDriver, None, None]:
    if web_driver_type == WebDriverTypeEnum.TOR_BROWSER:
        web_driver = _create_torbrowser_driver()
    elif web_driver_type == WebDriverTypeEnum.FIREFOX:
        web_driver = _create_firefox_driver()
    else:
        raise ValueError(f"Unexpected value {web_driver_type}")

    try:
        yield web_driver
    finally:
        try:
            web_driver.quit()
        except Exception:
            logging.exception("Error stopping driver")


# TODO(AD): This could eventually replace the navigation/driver code in FunctionalTest
class _NavigationHelper:

    _TIMEOUT = 10
    _POLL_FREQUENCY = 0.1

    def __init__(self, web_driver: WebDriver) -> None:
        self.driver = web_driver

    def wait_for(self, function_with_assertion, timeout=_TIMEOUT):
        """Polling wait for an arbitrary assertion."""
        # Thanks to
        # http://chimera.labs.oreilly.com/books/1234000000754/ch20.html#_a_common_selenium_problem_race_conditions
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(self._POLL_FREQUENCY)
        # one more try, which will raise any errors if they are outstanding
        return function_with_assertion()

    def safe_click_by_id(self, element_id):
        """
        Clicks the element with the given ID attribute.

        Returns:
            el: The element, if found.

        Raises:
            selenium.common.exceptions.TimeoutException: If the element cannot be found in time.

        """
        el = WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
            expected_conditions.element_to_be_clickable((By.ID, element_id))
        )
        el.location_once_scrolled_into_view
        el.click()
        return el

    def safe_click_by_css_selector(self, selector):
        """
        Clicks the first element with the given CSS selector.

        Returns:
            el: The element, if found.

        Raises:
            selenium.common.exceptions.TimeoutException: If the element cannot be found in time.

        """
        el = WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        el.click()
        return el

    def safe_click_all_by_css_selector(self, selector, root=None):
        """
        Clicks each element that matches the given CSS selector.

        Returns:
            els (list): The list of elements that matched the selector.

        Raises:
            selenium.common.exceptions.TimeoutException: If the element cannot be found in time.

        """
        if root is None:
            root = self.driver
        els = self.wait_for(lambda: root.find_elements_by_css_selector(selector))
        for el in els:
            clickable_el = WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
                expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            clickable_el.click()
        return els

    def safe_send_keys_by_id(self, element_id, text):
        """
        Sends the given text to the element with the specified ID.

        Returns:
            el: The element, if found.

        Raises:
            selenium.common.exceptions.TimeoutException: If the element cannot be found in time.

        """
        el = WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
            expected_conditions.element_to_be_clickable((By.ID, element_id))
        )
        el.send_keys(text)
        return el

    def safe_send_keys_by_css_selector(self, selector, text):
        """
        Sends the given text to the first element with the given CSS selector.

        Returns:
            el: The element, if found.

        Raises:
            selenium.common.exceptions.TimeoutException: If the element cannot be found in time.

        """
        el = WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        el.send_keys(text)
        return el

    def alert_wait(self, timeout=_TIMEOUT * 10):
        WebDriverWait(self.driver, timeout, self._POLL_FREQUENCY).until(
            expected_conditions.alert_is_present(), "Timed out waiting for confirmation popup."
        )

    def alert_accept(self):
        # adapted from https://stackoverflow.com/a/34795883/837471
        def alert_is_not_present(object):
            """Expect an alert to not be present."""
            try:
                alert = self.driver.switch_to.alert
                alert.text
                return False
            except NoAlertPresentException:
                return True

        self.driver.switch_to.alert.accept()
        WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
            alert_is_not_present, "Timed out waiting for confirmation popup to disappear."
        )


# TODO(AD): This could eventually replace the SourceNavigationStepsMixin
class SourceAppNagivator:
    def __init__(
        self,
        source_app_base_url: str,
        web_driver: WebDriver,
        accept_languages: Optional[str] = None,
    ) -> None:
        self._source_app_base_url = source_app_base_url
        self._nav_helper = _NavigationHelper(web_driver)
        self.driver = web_driver
        self._accept_languages = accept_languages

    def _is_on_source_homepage(self):
        return self._nav_helper.wait_for(lambda: self.driver.find_element_by_id("source-index"))

    def source_visits_source_homepage(self):
        self.driver.get(self._source_app_base_url)
        assert self._is_on_source_homepage()

    def _is_on_generate_page(self):
        return self._nav_helper.wait_for(lambda: self.driver.find_element_by_id("create-form"))

    def source_clicks_submit_documents_on_homepage(self):
        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        self._nav_helper.safe_click_by_id("submit-documents-button")

        # The source should now be on the page where they are presented with
        # a diceware codename they can use for subsequent logins
        assert self._is_on_generate_page()

    def source_continues_to_submit_page(self, files_allowed=True):
        self._nav_helper.safe_click_by_id("continue-button")

        def submit_page_loaded():
            if not self._accept_languages:
                headline = self.driver.find_element_by_class_name("headline")
                if files_allowed:
                    assert "Submit Files or Messages" == headline.text
                else:
                    assert "Submit Messages" == headline.text

        self._nav_helper.wait_for(submit_page_loaded)
