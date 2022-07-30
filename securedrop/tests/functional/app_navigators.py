import gzip
import tempfile
import time
from contextlib import contextmanager
from random import randint
from typing import Dict, Generator, Iterable, List, Optional, Tuple

import pyotp
import requests
from encryption import EncryptionManager
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tests.functional.tor_utils import proxies_for_url
from tests.functional.web_drivers import WebDriverTypeEnum, get_web_driver
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

    def safe_click_by_id(self, element_id: str) -> WebElement:
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

    def safe_click_by_css_selector(self, selector: str) -> WebElement:
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

    def safe_click_all_by_css_selector(self, selector: str) -> List[WebElement]:
        """
        Clicks each element that matches the given CSS selector.

        Returns:
            els (list): The list of elements that matched the selector.

        Raises:
            selenium.common.exceptions.TimeoutException: If the element cannot be found in time.

        """
        els = self.wait_for(lambda: self.driver.find_elements_by_css_selector(selector))
        for el in els:
            clickable_el = WebDriverWait(self.driver, self._TIMEOUT, self._POLL_FREQUENCY).until(
                expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            clickable_el.click()
        return els

    def safe_send_keys_by_id(self, element_id: str, text: str) -> WebElement:
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

    def safe_send_keys_by_css_selector(self, selector: str, text: str) -> WebElement:
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

    def alert_wait(self, timeout: int = _TIMEOUT * 10) -> None:
        WebDriverWait(self.driver, timeout, self._POLL_FREQUENCY).until(
            expected_conditions.alert_is_present(), "Timed out waiting for confirmation popup."
        )

    def alert_accept(self) -> None:
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

    def _is_on_generate_page(self) -> WebElement:
        return self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("source-generate"))

    def source_clicks_submit_documents_on_homepage(self) -> None:
        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        self.nav_helper.safe_click_by_css_selector("#started-form button")

        # The source should now be on the page where they are presented with
        # a diceware codename they can use for subsequent logins
        assert self._is_on_generate_page()

    def source_continues_to_submit_page(self) -> None:
        self.nav_helper.safe_click_by_css_selector("#create-form button")

        def submit_page_loaded() -> None:
            if not self.accept_languages:
                headline = self.driver.find_element_by_id("submit-heading")
                # Message will either be "Submit Messages" or "Submit Files or Messages" depending
                #  on whether file uploads are allowed by the instance's config
                assert "Submit" in headline.text
                assert "Messages" in headline.text

        self.nav_helper.wait_for(submit_page_loaded)

    def _is_on_logout_page(self) -> WebElement:
        return self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("source-logout"))

    def source_logs_out(self) -> None:
        self.nav_helper.safe_click_by_id("logout")
        assert self._is_on_logout_page()

    def source_retrieves_codename_from_hint(self) -> str:
        # We use inputs to change CSS states for subsequent elements in the DOM, if it is unchecked
        # the codename is hidden
        content = self.driver.find_element_by_id("codename-show-checkbox")
        assert content.get_attribute("checked") is None

        self.nav_helper.safe_click_by_id("codename-show")

        assert content.get_attribute("checked") is not None
        content_content = self.driver.find_element_by_css_selector("#codename span")
        return content_content.text

    def source_chooses_to_login(self) -> None:
        self.nav_helper.safe_click_by_css_selector("#return-visit a")
        self.nav_helper.wait_for(lambda: self.driver.find_elements_by_id("source-login"))

    def _is_logged_in(self) -> WebElement:
        return self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("logout"))

    def source_proceeds_to_login(self, codename: str) -> None:
        self.nav_helper.safe_send_keys_by_id("codename", codename)
        self.nav_helper.safe_click_by_css_selector(".form-controls button")

        # Check that we've logged in
        assert self._is_logged_in()

        replies = self.driver.find_elements_by_id("replies")
        assert len(replies) == 1

    def source_submits_a_message(self, message: str = "S3cr3t m3ss4ge") -> str:
        # Write the message to submit
        self.nav_helper.safe_send_keys_by_id("msg", message)

        # Hit the submit button
        self.nav_helper.safe_click_by_css_selector(".form-controls button")

        # Wait for confirmation that the message was submitted
        def message_submitted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_css_selector(".success")
                assert "Thank" in notification.text
                return notification.text

        # Return the confirmation notification
        notification_text = self.nav_helper.wait_for(message_submitted)
        return notification_text

    def source_submits_a_file(self, file_content: str = "S3cr3t f1l3") -> None:
        # Write the content to a file
        with tempfile.NamedTemporaryFile() as file:
            file.write(file_content.encode("utf-8"))
            file.seek(0)
            filename = file.name

            # Submit the file
            self.nav_helper.safe_send_keys_by_id("fh", filename)
            self.nav_helper.safe_click_by_css_selector(".form-controls button")

            def file_submitted() -> None:
                if not self.accept_languages:
                    notification = self.driver.find_element_by_css_selector(".success")
                    expected_notification = "Thank you for sending this information to us"
                    assert expected_notification in notification.text

            # Allow extra time for file uploads
            self.nav_helper.wait_for(file_submitted, timeout=15)

            # allow time for reply key to be generated
            time.sleep(3)


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

    def is_on_journalist_homepage(self) -> WebElement:
        return self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_css_selector("div.journalist-view-all")
        )

    def journalist_logs_in(
        self,
        username: str,
        password: str,
        otp_secret: str,
        is_login_expected_to_succeed: bool = True,
    ) -> None:
        # Submit the login form
        self.driver.get(f"{self._journalist_app_base_url}/login")
        self.nav_helper.safe_send_keys_by_css_selector('input[name="username"]', username)
        self.nav_helper.safe_send_keys_by_css_selector('input[name="password"]', password)
        otp = pyotp.TOTP(otp_secret)
        self.nav_helper.safe_send_keys_by_css_selector('input[name="token"]', str(otp.now()))
        self.nav_helper.safe_click_by_css_selector('button[type="submit"]')

        if not is_login_expected_to_succeed:
            return

        # Successful login should redirect to the index
        self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("link-logout"))
        assert self.is_on_journalist_homepage()

    def journalist_checks_messages(self) -> None:
        self.driver.get(self._journalist_app_base_url)

        # There should be 1 collection in the list of collections
        collections_count = self.count_sources_on_index_page()
        assert collections_count == 1

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
        self.journalist_selects_the_first_source()
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

    def journalist_selects_the_first_source(self) -> None:
        self.driver.find_element_by_css_selector("#un-starred-source-link-1").click()

    def journalist_composes_reply_to_source(self, reply_content: str) -> None:
        self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("reply-text-field"))
        self.nav_helper.safe_send_keys_by_id("reply-text-field", reply_content)

    def journalist_sends_reply_to_source(
        self, reply_content: str = "Thanks for the documents. Can you submit more? éè"
    ) -> None:
        self.journalist_composes_reply_to_source(reply_content=reply_content)
        self.driver.find_element_by_id("reply-button").click()

        def reply_stored() -> None:
            if not self.accept_languages:
                assert "The source will receive your reply" in self.driver.page_source

        self.nav_helper.wait_for(reply_stored)

    def journalist_visits_col(self) -> None:
        self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_css_selector("table#collections")
        )
        self.nav_helper.safe_click_by_id("un-starred-source-link-1")
        self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_css_selector("table#submissions")
        )

    def journalist_selects_first_doc(self) -> None:
        self.nav_helper.safe_click_by_css_selector(
            'input[type="checkbox"][name="doc_names_selected"]'
        )

        self.nav_helper.wait_for(
            lambda: expected_conditions.element_located_to_be_selected(
                (By.CSS_SELECTOR, 'input[type="checkbox"][name="doc_names_selected"]')
            )
        )

        assert self.driver.find_element_by_css_selector(
            'input[type="checkbox"][name="doc_names_selected"]'
        ).is_selected()

    def journalist_clicks_delete_selected_link(self) -> None:
        self.nav_helper.safe_click_by_css_selector("a#delete-selected-link")
        self.nav_helper.wait_for(
            lambda: self.driver.find_element_by_id("delete-selected-confirmation-modal")
        )

    def journalist_clicks_delete_all_and_sees_confirmation(self) -> None:
        self.nav_helper.safe_click_all_by_css_selector("[name=doc_names_selected]")
        self.nav_helper.safe_click_by_css_selector("a#delete-selected-link")

    def journalist_confirms_delete_selected(self) -> None:
        self.nav_helper.wait_for(
            lambda: expected_conditions.element_to_be_clickable((By.ID, "delete-selected"))
        )
        confirm_btn = self.driver.find_element_by_id("delete-selected")
        confirm_btn.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(confirm_btn).click().perform()

    def get_submission_checkboxes_on_current_page(self):
        checkboxes = self.driver.find_elements_by_name("doc_names_selected")
        return checkboxes

    def count_submissions_on_current_page(self) -> int:
        return len(self.get_submission_checkboxes_on_current_page())

    def get_sources_on_index_page(self):
        assert self.is_on_journalist_homepage()
        sources = self.driver.find_elements_by_class_name("code-name")
        return sources

    def count_sources_on_index_page(self) -> int:
        return len(self.get_sources_on_index_page())

    def journalist_confirm_delete_selected(self) -> None:
        self.nav_helper.wait_for(
            lambda: expected_conditions.element_to_be_clickable((By.ID, "delete-selected"))
        )
        confirm_btn = self.driver.find_element_by_id("delete-selected")
        confirm_btn.location_once_scrolled_into_view
        ActionChains(self.driver).move_to_element(confirm_btn).click().perform()

    def journalist_sees_link_to_admin_page(self) -> bool:
        try:
            self.driver.find_element_by_id("link-admin-index")
            return True
        except NoSuchElementException:
            return False

    def admin_visits_admin_interface(self) -> None:
        self.nav_helper.safe_click_by_id("link-admin-index")
        self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("add-user"))

    def admin_creates_a_user(
        self,
        username: Optional[str] = None,
        is_admin: bool = False,
        is_user_creation_expected_to_succeed: bool = True,
    ) -> Optional[Tuple[str, str, str]]:
        self.nav_helper.safe_click_by_id("add-user")
        self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("username"))

        if not self.accept_languages:
            # The add user page has a form with an "ADD USER" button
            btns = self.driver.find_elements_by_tag_name("button")
            assert "ADD USER" in [el.text for el in btns]

        password = self.driver.find_element_by_css_selector("#password").text.strip()
        if not username:
            final_username = f"journalist{str(randint(1000, 1000000))}"
        else:
            final_username = username

        self._fill_and_submit_user_creation_form(
            username=final_username,
            is_admin=is_admin,
        )

        if not is_user_creation_expected_to_succeed:
            return None

        self.nav_helper.wait_for(lambda: self.driver.find_element_by_id("check-token"))

        if not self.accept_languages:
            # Clicking submit on the add user form should redirect to
            # the FreeOTP page
            h1s = [h1.text for h1 in self.driver.find_elements_by_tag_name("h1")]
            assert "Enable FreeOTP" in h1s

        otp_secret = (
            self.driver.find_element_by_css_selector("#shared-secret").text.strip().replace(" ", "")
        )
        totp = pyotp.TOTP(otp_secret)

        self.nav_helper.safe_send_keys_by_css_selector('input[name="token"]', str(totp.now()))
        self.nav_helper.safe_click_by_css_selector("button[type=submit]")

        # Verify the two-factor authentication
        def user_token_added():
            if not self.accept_languages:
                # Successfully verifying the code should redirect to the admin
                # interface, and flash a message indicating success
                flash_msg = self.driver.find_elements_by_css_selector(".flash")
                expected_msg = (
                    f'The two-factor code for user "{final_username}"'
                    f" was verified successfully."
                )
                assert expected_msg in [el.text for el in flash_msg]

        self.nav_helper.wait_for(user_token_added)
        return final_username, password, otp_secret

    def _fill_and_submit_user_creation_form(
        self, username: str, is_admin: bool, hotp: Optional[str] = None
    ) -> None:
        self.nav_helper.safe_send_keys_by_css_selector('input[name="username"]', username)

        if hotp:
            self.nav_helper.safe_click_all_by_css_selector('input[name="is_hotp"]')
            self.nav_helper.safe_send_keys_by_css_selector('input[name="otp_secret"]', hotp)

        if is_admin:
            self.nav_helper.safe_click_by_css_selector('input[name="is_admin"]')

        self.nav_helper.safe_click_by_css_selector("button[type=submit]")

    def journalist_logs_out(self) -> None:
        # Click the logout link
        self.nav_helper.safe_click_by_id("link-logout")
        self.nav_helper.wait_for(lambda: self.driver.find_element_by_css_selector(".login-form"))

        # Logging out should redirect back to the login page
        def login_page():
            assert "Login to access the journalist interface" in self.driver.page_source

        self.nav_helper.wait_for(login_page)

    def admin_visits_system_config_page(self):
        self.nav_helper.safe_click_by_id("update-instance-config")

        def config_page_loaded():
            assert self.driver.find_element_by_id("test-ossec-alert")

        self.nav_helper.wait_for(config_page_loaded)

    def journalist_visits_edit_account(self):
        self.nav_helper.safe_click_by_id("link-edit-account")
