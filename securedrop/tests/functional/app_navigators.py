import gzip
import tempfile
import time
from contextlib import contextmanager

from typing import Optional, Dict, Iterable, Generator

import pyotp
import requests
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from tests.functional.web_drivers import get_web_driver, WebDriverTypeEnum

from encryption import EncryptionManager
from tests.functional.tor_utils import proxies_for_url
from tests.test_encryption import import_journalist_private_key


# TODO(AD): This is intended to eventually replace the navigation/driver code in FunctionalTest
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


# TODO(AD): This is intended to eventually replace the SourceNavigationStepsMixin
class SourceAppNagivator:
    def __init__(
        self,
        source_app_base_url: str,
        web_driver: WebDriver,
        accept_languages: Optional[str] = None,
    ) -> None:
        self._source_app_base_url = source_app_base_url
        self.nav_helper = _NavigationHelper(web_driver)
        self.driver = web_driver
        self.accept_languages = accept_languages

    @classmethod
    @contextmanager
    def using_tor_browser_web_driver(
        cls,
        source_app_base_url: str,
        accept_languages: Optional[str] = None,
    ) -> Generator["SourceAppNagivator", None, None]:
        """Convenience method for auto-creating the web driver to be used by the navigator."""
        with get_web_driver(
            web_driver_type=WebDriverTypeEnum.TOR_BROWSER,
            accept_languages=accept_languages,
        ) as tor_browser_web_driver:
            yield cls(
                source_app_base_url=source_app_base_url,
                web_driver=tor_browser_web_driver,
                accept_languages=accept_languages,
            )

    def _is_on_source_homepage(self) -> WebElement:
        return self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("source-index"))

    def source_visits_source_homepage(self) -> None:
        self.driver.get(self._source_app_base_url)
        assert self._is_on_source_homepage()

    def _is_on_lookup_page(self) -> WebElement:
        return self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("source-lookup"))

    def source_clicks_submit_documents_on_homepage(self) -> None:
        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        self.nav_helper.safe_click_by_css_selector("#started-form button")

        # The source should now be on the lookup page where they can submit
        # docs/messages. They will get a passphrase after their first submission.
        assert self._is_on_lookup_page()

    def source_continues_to_submit_page(self) -> None:

        def submit_page_loaded() -> None:
            if not self.accept_languages:
                headline = self.driver.find_element_by_id("welcome-heading")
                assert "Welcome!" == headline.text

        self.nav_helper.wait_for(submit_page_loaded)

    def _is_on_logout_page(self) -> WebElement:
        return self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_id("source-logout")
        )

    def source_logs_out(self) -> None:
        self.nav_helper.safe_click_by_id("logout")
        assert self._is_on_logout_page()

    def source_retrieves_codename_from_hint(self) -> str:
        # We use inputs to change CSS states for subsequent elements in the DOM, if it is unchecked
        content = self.driver.find_element_by_id("passphrase-show-checkbox")

        # TODO: should the codename be hidden by default under inverted flow?
        # assert content.get_attribute("checked") is None
        # self.nav_helper.safe_click_by_id("codename-show")

        assert content.get_attribute("checked") is not None
        content_content = self.driver.find_element_by_css_selector("#passphrase span")
        return content_content.text

    def source_chooses_to_login(self) -> None:
        self.nav_helper.safe_click_by_css_selector("#return-visit a")
        self.nav_helper.wait_for(
            lambda: self.driver.find_elements_by_id("source-login")
        )

    def _is_logged_in(self) -> WebElement:
        return self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("logout"))

    def source_proceeds_to_login(self, codename: str) -> None:
        self.nav_helper.safe_send_keys_by_id("passphrase", codename)
        self.nav_helper.safe_click_by_css_selector(".form-controls button")

        # Check that we've logged in
        assert self._is_logged_in()

        replies = self.driver.find_elements_by_id("replies")
        assert len(replies) == 1

    def source_submits_a_message(
                                 self,
                                 message: str = "S3cr3t m3ss4ge",
                                 will_succeed: bool = True
                                 ) -> str:
        # Write the message to submit
        self.nav_helper.safe_send_keys_by_css_selector("[name=msg]", message)

        # Hit the submit button
        self.nav_helper.safe_click_by_css_selector(".form-controls button")

        # Wait for confirmation that the message was submitted
        def message_submitted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_css_selector(".success")
                assert "Thank" in notification.text
                return notification.text

        # If it's expected that the submission will fail, wait for an error
        # notificaition
        def message_failed():
            if not self.accept_languages:
                notification = self.driver.find_element_by_css_selector(".error")
                assert len(notification.text) > 0
                return notification.text

        # Return the confirmation notification
        if will_succeed:
            notification_text = self.nav_helper.wait_for(message_submitted)
            return notification_text
        else:
            notification_text = self.nav_helper.wait_for(message_failed)
            return notification_text

    def source_sees_flash_message(self) -> str:
        notification = self.driver.find_element_by_css_selector(".notification")
        assert notification
        return notification


# TODO(AD): This is intended to eventually replace the JournalistNavigationStepsMixin
class JournalistAppNavigator:
    def __init__(
        self,
        journalist_app_base_url: str,
        web_driver: WebDriver,
        accept_languages: Optional[str] = None,
    ) -> None:
        self._journalist_app_base_url = journalist_app_base_url
        self.nav_helper = _NavigationHelper(web_driver)
        self.driver = web_driver
        self.accept_languages = accept_languages

    def _is_on_journalist_homepage(self):
        return self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_css_selector("div.journalist-view-all")
        )

    def journalist_logs_in(self, username: str, password: str, otp_secret: str) -> None:
        otp = pyotp.TOTP(otp_secret)
        token = str(otp.now())
        for i in range(3):
            # Submit the login form
            self.driver.get(f"{self._journalist_app_base_url}/login")
            self.nav_helper.safe_send_keys_by_css_selector('input[name="username"]', username)
            self.nav_helper.safe_send_keys_by_css_selector('input[name="password"]', password)
            self.nav_helper.safe_send_keys_by_css_selector('input[name="token"]', token)
            self.nav_helper.safe_click_by_css_selector('button[type="submit"]')

            # Successful login should redirect to the index
            self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("link-logout"))
            if self.driver.current_url != self._journalist_app_base_url:
                new_token = str(otp.now())
                while token == new_token:
                    time.sleep(1)
                    new_token = str(otp.now())
                token = new_token
            else:
                break

        assert self._is_on_journalist_homepage()

    def journalist_checks_messages(self):
        self.driver.get(self._journalist_app_base_url)

        # There should be 1 collection in the list of collections
        code_names = self.driver.find_elements_by_class_name("code-name")
        assert 0 != len(code_names), code_names
        assert 1 <= len(code_names), code_names

        if not self.accept_languages:
            # There should be a "1 unread" span in the sole collection entry
            unread_span = self.driver.find_element_by_css_selector("tr.unread")
            assert "1 unread" in unread_span.text

    @staticmethod
    def _download_content_at_url(url: str, cookies: Dict[str, str]) -> bytes:
        r = requests.get(url, cookies=cookies, proxies=proxies_for_url(url), stream=True)
        if r.status_code != 200:
            raise Exception("Failed to download the data.")
        data = b""
        for chunk in r.iter_content(1024):
            data += chunk
        return data

    @staticmethod
    def _unzip_content(raw_content: bytes) -> str:
        with tempfile.TemporaryFile() as fp:
            fp.write(raw_content)
            fp.seek(0)

            gzf = gzip.GzipFile(mode="rb", fileobj=fp)
            content = gzf.read()

        return content.decode("utf-8")

    def journalist_downloads_first_message(
        self, encryption_mgr_to_use_for_decryption: EncryptionManager
    ) -> str:
        # Select the first submission from the first source in the page
        self._journalist_selects_the_first_source()
        self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_css_selector("table#submissions")
        )
        submissions = self.driver.find_elements_by_css_selector("#submissions a")
        assert 1 == len(submissions)
        file_url = submissions[0].get_attribute("href")

        # Downloading files with Selenium is tricky because it cannot automate
        # the browser's file download dialog. We can directly request the file
        # using requests, but we need to pass the cookies for logged in user
        # for Flask to allow this.
        def cookie_string_from_selenium_cookies(
            cookies: Iterable[Dict[str, str]]
        ) -> Dict[str, str]:
            result = {}
            for cookie in cookies:
                result[cookie["name"]] = cookie["value"]
            return result

        cks = cookie_string_from_selenium_cookies(self.driver.get_cookies())
        raw_content = self._download_content_at_url(file_url, cks)

        with import_journalist_private_key(encryption_mgr_to_use_for_decryption):
            decryption_result = encryption_mgr_to_use_for_decryption._gpg.decrypt(raw_content)

        if file_url.endswith(".gz.gpg"):
            decrypted_message = self._unzip_content(decryption_result.data)
        else:
            decrypted_message = decryption_result.data.decode("utf-8")

        return decrypted_message

    def _journalist_selects_the_first_source(self) -> None:
        self.driver.find_element_by_css_selector("#un-starred-source-link-1").click()
