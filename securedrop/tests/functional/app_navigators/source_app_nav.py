import tempfile
import time
from contextlib import contextmanager
from typing import Generator, Optional

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from tests.functional.app_navigators._nav_helper import NavigationHelper
from tests.functional.web_drivers import WebDriverTypeEnum, get_web_driver


class SourceAppNavigator:
    """Helper functions to navigate the source app when implementing functional/selenium tests.

    Only logic that needs to be shared across multiple tests within different files should be
    added to this class, in order to keep this class as small as possible.
    """

    def __init__(
        self,
        source_app_base_url: str,
        web_driver: WebDriver,
        accept_languages: Optional[str] = None,
    ) -> None:
        self._source_app_base_url = source_app_base_url
        self.nav_helper = NavigationHelper(web_driver)
        self.driver = web_driver
        self.accept_languages = accept_languages

    @classmethod
    @contextmanager
    def using_tor_browser_web_driver(
        cls,
        source_app_base_url: str,
        accept_languages: Optional[str] = None,
    ) -> Generator["SourceAppNavigator", None, None]:
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
