import logging
from pathlib import Path
from typing import Generator, Tuple
from uuid import uuid4

import pytest
from models import Journalist
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.app_navigators.source_app_nav import SourceAppNavigator
from tests.functional.conftest import SdServersFixtureResult, spawn_sd_servers
from tests.functional.db_session import get_database_session
from tests.functional.factories import SecureDropConfigFactory
from tests.functional.sd_config_v2 import SecureDropConfig


class TestAdminInterfaceAddUser:
    def test_admin_adds_non_admin_user(self, sd_servers_with_clean_state, firefox_web_driver):
        # Given an SD server
        # And a journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_clean_state.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # Then they see the same interface as a normal user, since there may be users who wish to
        # be both journalists and admins
        assert journ_app_nav.is_on_journalist_homepage()

        # And they see a link that take them to the admin page
        assert journ_app_nav.journalist_sees_link_to_admin_page()

        # And when they go to the admin page to add a new non-admin user
        journ_app_nav.admin_visits_admin_interface()
        result = journ_app_nav.admin_creates_a_user(is_admin=False)
        new_user_username, new_user_pw, new_user_otp_secret = result

        # Then it succeeds

        # Log the admin user out
        journ_app_nav.journalist_logs_out()
        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_css_selector(".login-form")
        )

        # And when the new user tries to login
        journ_app_nav.journalist_logs_in(
            username=new_user_username,
            password=new_user_pw,
            otp_secret=new_user_otp_secret,
        )

        # It succeeds
        # And since the new user is not an admin, they don't see a link to the admin page
        assert not journ_app_nav.journalist_sees_link_to_admin_page()

    def test_admin_adds_admin_user(self, sd_servers_with_clean_state, firefox_web_driver):
        # Given an SD server
        # And the first journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_clean_state.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # When they go to the admin page to add a new admin user
        journ_app_nav.admin_visits_admin_interface()
        result = journ_app_nav.admin_creates_a_user(is_admin=True)
        new_user_username, new_user_pw, new_user_otp_secret = result

        # Then it succeeds

        # Log the admin user out
        journ_app_nav.journalist_logs_out()
        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_css_selector(".login-form")
        )

        # And when the new user tries to login
        journ_app_nav.journalist_logs_in(
            username=new_user_username,
            password=new_user_pw,
            otp_secret=new_user_otp_secret,
        )

        # It succeeds
        # And since the new user is an admin, they see a link to the admin page
        assert journ_app_nav.journalist_sees_link_to_admin_page()

    def test_admin_adds_user_with_invalid_username(
        self, sd_servers_with_clean_state, firefox_web_driver
    ):
        # Given an SD server
        # And the first journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_clean_state.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # When they go to the admin page to add a new admin user with an invalid name
        journ_app_nav.admin_visits_admin_interface()

        # We use a callback and an exception to stop after the form was submitted
        class StopAfterFormSubmitted(Exception):
            pass

        def submit_form_and_stop():
            journ_app_nav.nav_helper.safe_click_by_css_selector("button[type=submit]")
            raise StopAfterFormSubmitted()

        try:
            journ_app_nav.admin_creates_a_user(
                username="deleted", callback_before_submitting_add_user_step=submit_form_and_stop
            )
        except StopAfterFormSubmitted:
            pass

        # Then it fails with an error
        error_msg = journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_css_selector(".form-validation-error")
        )

        # And they see the corresponding error message
        assert (
            "This username is invalid because it is reserved for internal use "
            "by the software." in error_msg.text
        )


# Tests for editing a user need a second journalist user to be created
_SECOND_JOURNALIST_USERNAME = "second_journalist"
_SECOND_JOURNALIST_PASSWORD = "shivering reliance sadness crinkly landmass wafer deceit"
_SECOND_JOURNALIST_OTP_SECRET = "TVWT452VLMS7KAVZ"


def _create_second_journalist(config_in_use: SecureDropConfig) -> None:
    # Add a test journalist
    with get_database_session(database_uri=config_in_use.DATABASE_URI) as db_session_for_sd_servers:
        journalist = Journalist(
            username=_SECOND_JOURNALIST_USERNAME,
            password=_SECOND_JOURNALIST_PASSWORD,
            is_admin=False,
        )
        journalist.otp_secret = _SECOND_JOURNALIST_OTP_SECRET
        db_session_for_sd_servers.add(journalist)
        db_session_for_sd_servers.commit()


@pytest.fixture(scope="function")
def sd_servers_with_second_journalist(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SdServersFixtureResult, None, None]:
    """Sams as sd_servers but spawns the apps with an already-created second journalist.

    Slower than sd_servers as it is function-scoped.
    """
    default_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/functional-with-second-journnalist-{uuid4()}"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(default_config.GPG_KEY_DIR) == gpg_dir
    assert default_config.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes with a callback to create a submission
    with spawn_sd_servers(
        config_to_use=default_config, journalist_app_setup_callback=_create_second_journalist
    ) as sd_servers_result:
        yield sd_servers_result


class TestAdminInterfaceEditAndDeleteUser:
    """Test editing another journalist/user.

    Note: Tests to edit a user's 2fa secret are implemented in TestJournalistLayoutAdmin.
    """

    @staticmethod
    def _admin_logs_in_and_goes_to_edit_page_for_second_journalist(
        sd_servers_result: SdServersFixtureResult,
        firefox_web_driver: WebDriver,
    ) -> JournalistAppNavigator:
        # Log in as the admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_result.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_result.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_result.journalist_username,
            password=sd_servers_result.journalist_password,
            otp_secret=sd_servers_result.journalist_otp_secret,
        )

        journ_app_nav.admin_visits_admin_interface()

        # Go to the "edit user" page for the second journalist
        journ_app_nav.admin_visits_user_edit_page(
            username_of_journalist_to_edit=_SECOND_JOURNALIST_USERNAME
        )
        return journ_app_nav

    def test_admin_edits_username(self, sd_servers_with_second_journalist, firefox_web_driver):
        # Given an SD server with a second journalist created
        # And the first journalist logged into the journalist interface as an admin
        # And they went to the "edit user" page for the second journalist
        journ_app_nav = self._admin_logs_in_and_goes_to_edit_page_for_second_journalist(
            sd_servers_result=sd_servers_with_second_journalist,
            firefox_web_driver=firefox_web_driver,
        )

        # When they change the second journalist's username
        self._admin_edits_username_and_submits_form(journ_app_nav, new_username="new_name")

        # Then it succeeds
        def user_edited():
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "Account updated." in flash_msg.text

        journ_app_nav.nav_helper.wait_for(user_edited)

    def test_admin_edits_invalid_username(
        self, sd_servers_with_second_journalist, firefox_web_driver
    ):
        # Given an SD server with a second journalist created
        # And the first journalist logged into the journalist interface as an admin
        # And they went to the "edit user" page for the second journalist
        journ_app_nav = self._admin_logs_in_and_goes_to_edit_page_for_second_journalist(
            sd_servers_result=sd_servers_with_second_journalist,
            firefox_web_driver=firefox_web_driver,
        )

        # When they change the second journalist's username to an invalid username
        self._admin_edits_username_and_submits_form(journ_app_nav, new_username="deleted")

        # Then it fails
        def user_edited():
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "Invalid username" in flash_msg.text

        journ_app_nav.nav_helper.wait_for(user_edited)

    @staticmethod
    def _admin_edits_username_and_submits_form(
        journ_app_nav: JournalistAppNavigator,
        new_username: str,
    ) -> None:
        journ_app_nav.nav_helper.safe_send_keys_by_css_selector(
            'input[name="username"]', Keys.CONTROL + "a"
        )
        journ_app_nav.nav_helper.safe_send_keys_by_css_selector(
            'input[name="username"]', Keys.DELETE
        )
        journ_app_nav.nav_helper.safe_send_keys_by_css_selector(
            'input[name="username"]', new_username
        )
        journ_app_nav.nav_helper.safe_click_by_css_selector("button[type=submit]")

    def test_admin_resets_password(self, sd_servers_with_second_journalist, firefox_web_driver):
        # Given an SD server with a second journalist created
        # And the first journalist logged into the journalist interface as an admin
        # And they went to the "edit user" page for the second journalist
        journ_app_nav = self._admin_logs_in_and_goes_to_edit_page_for_second_journalist(
            sd_servers_result=sd_servers_with_second_journalist,
            firefox_web_driver=firefox_web_driver,
        )

        # When they reset the second journalist's password
        new_password = journ_app_nav.driver.find_element_by_css_selector("#password").text.strip()
        assert new_password
        reset_pw_btn = journ_app_nav.driver.find_element_by_css_selector("#reset-password")
        reset_pw_btn.click()

        # Then it succeeds
        # Wait until page refreshes to avoid causing a broken pipe error (#623)
        def update_password_success():
            assert "Password updated." in journ_app_nav.driver.page_source

        journ_app_nav.nav_helper.wait_for(update_password_success)

        # And the second journalist is able to login using the new password
        journ_app_nav.journalist_logs_out()
        journ_app_nav.journalist_logs_in(
            username=_SECOND_JOURNALIST_USERNAME,
            password=new_password,
            otp_secret=_SECOND_JOURNALIST_OTP_SECRET,
        )
        assert journ_app_nav.is_on_journalist_homepage()

    def test_admin_deletes_user(self, sd_servers_with_second_journalist, firefox_web_driver):
        # Given an SD server with a second journalist created
        # And the first journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_second_journalist.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_second_journalist.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_second_journalist.journalist_username,
            password=sd_servers_with_second_journalist.journalist_password,
            otp_secret=sd_servers_with_second_journalist.journalist_otp_secret,
        )

        # When the admin deletes the second journalist
        journ_app_nav.admin_visits_admin_interface()
        for i in range(15):
            try:
                journ_app_nav.nav_helper.safe_click_by_css_selector(".delete-user a")
                journ_app_nav.nav_helper.wait_for(
                    lambda: expected_conditions.element_to_be_clickable((By.ID, "delete-selected"))
                )
                journ_app_nav.nav_helper.safe_click_by_id("delete-selected")
                journ_app_nav.nav_helper.alert_wait()
                journ_app_nav.nav_helper.alert_accept()
                break
            except TimeoutException:
                # Selenium has failed to click, and the confirmation
                # alert didn't happen. Try once more.
                logging.info("Selenium has failed to click yet again; retrying.")

        # Then it succeeds
        def user_deleted():
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "Deleted user" in flash_msg.text

        journ_app_nav.nav_helper.wait_for(user_deleted)


class TestAdminInterfaceEditConfig:
    """Test the instance's system settings.

    Note: Additional/related tests are also implemented in TestAdminLayoutEditConfig.
    """

    def test_disallow_file_submission(
        self, sd_servers_with_clean_state, firefox_web_driver, tor_browser_web_driver
    ):
        # Given an SD server
        # And a journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_clean_state.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # And they go to the admin config page
        journ_app_nav.admin_visits_admin_interface()
        journ_app_nav.admin_visits_system_config_page()

        # When they disallow file uploads, then it succeeds
        self._admin_updates_document_upload_instance_setting(
            instance_should_allow_file_uploads=False,
            journ_app_nav=journ_app_nav,
        )

        # And then, when a source user tries to upload a file
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers_with_clean_state.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )
        source_app_nav.source_visits_source_homepage()
        source_app_nav.source_clicks_submit_documents_on_homepage()
        source_app_nav.source_continues_to_submit_page()

        # Then they don't see the option to upload a file because uploads were disallowed
        with pytest.raises(NoSuchElementException):
            source_app_nav.driver.find_element_by_class_name("attachment")

    @classmethod
    def _admin_updates_document_upload_instance_setting(
        cls,
        instance_should_allow_file_uploads: bool,
        journ_app_nav: JournalistAppNavigator,
    ) -> None:
        # Retrieve the instance's current upload setting
        upload_element_id = "prevent_document_uploads"
        instance_currently_allows_file_uploads = not journ_app_nav.driver.find_element_by_id(
            upload_element_id
        ).is_selected()

        # Ensure the new setting is different from the existing setting
        assert instance_currently_allows_file_uploads != instance_should_allow_file_uploads

        # Update the instance's upload setting
        journ_app_nav.nav_helper.safe_click_by_id(upload_element_id)
        journ_app_nav.nav_helper.safe_click_by_id("submit-submission-preferences")
        cls._admin_submits_instance_settings_form(journ_app_nav)

    @staticmethod
    def _admin_submits_instance_settings_form(journ_app_nav: JournalistAppNavigator) -> None:
        def preferences_saved():
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "Preferences saved." in flash_msg.text

        journ_app_nav.nav_helper.wait_for(preferences_saved, timeout=20)

    def test_allow_file_submission(
        self, sd_servers_with_clean_state, firefox_web_driver, tor_browser_web_driver
    ):
        # Given an SD server
        # And a journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_clean_state.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # And they go to the admin config page
        journ_app_nav.admin_visits_admin_interface()
        journ_app_nav.admin_visits_system_config_page()

        # And the instance is configured to disallow file uploads
        self._admin_updates_document_upload_instance_setting(
            instance_should_allow_file_uploads=False,
            journ_app_nav=journ_app_nav,
        )

        # When they re-allow file uploads, then it succeeds
        self._admin_updates_document_upload_instance_setting(
            instance_should_allow_file_uploads=True,
            journ_app_nav=journ_app_nav,
        )

        # And then, when a source user tries to upload a file
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers_with_clean_state.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )
        source_app_nav.source_visits_source_homepage()
        source_app_nav.source_clicks_submit_documents_on_homepage()
        source_app_nav.source_continues_to_submit_page()

        # Then they see the option to upload a file because uploads were allowed
        assert source_app_nav.driver.find_element_by_class_name("attachment")

    def test_orgname_is_changed(
        self, sd_servers_with_clean_state, firefox_web_driver, tor_browser_web_driver
    ):
        # Given an SD server
        # And a journalist logged into the journalist interface as an admin
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_clean_state.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        assert sd_servers_with_clean_state.journalist_is_admin
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_clean_state.journalist_username,
            password=sd_servers_with_clean_state.journalist_password,
            otp_secret=sd_servers_with_clean_state.journalist_otp_secret,
        )

        # And they go to the admin config page
        journ_app_nav.admin_visits_admin_interface()
        journ_app_nav.admin_visits_system_config_page()

        # When they update the organization's name
        assert "SecureDrop" == journ_app_nav.driver.title
        journ_app_nav.driver.find_element_by_id("organization_name").clear()
        new_org_name = "Walden Inquirer"
        journ_app_nav.nav_helper.safe_send_keys_by_id("organization_name", new_org_name)
        journ_app_nav.nav_helper.safe_click_by_id("submit-update-org-name")
        self._admin_submits_instance_settings_form(journ_app_nav)

        # Then it succeeds
        assert new_org_name == journ_app_nav.driver.title

        # And then, when a source user logs into the source app
        source_app_nav = SourceAppNavigator(
            source_app_base_url=sd_servers_with_clean_state.source_app_base_url,
            web_driver=tor_browser_web_driver,
        )

        # THey see the new organization name in the homepage
        source_app_nav.source_visits_source_homepage()
        assert new_org_name in source_app_nav.driver.title

        # And in the submission page
        source_app_nav.source_clicks_submit_documents_on_homepage()
        source_app_nav.source_continues_to_submit_page()
        assert new_org_name in source_app_nav.driver.title
