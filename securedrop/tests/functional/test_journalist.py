#
# SecureDrop whistleblower submission system
# Copyright (C) 2017 Loic Dachary <loic@dachary.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from pathlib import Path
from typing import Generator, Tuple
from uuid import uuid4

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from tests.functional.app_navigators.journalist_app_nav import JournalistAppNavigator
from tests.functional.conftest import (
    SdServersFixtureResult,
    create_source_and_submission,
    spawn_sd_servers,
)
from tests.functional.factories import SecureDropConfigFactory
from tests.functional.sd_config_v2 import SecureDropConfig


class TestJournalist:
    def test_journalist_verifies_deletion_of_one_submission_modal(
        self, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_submitted_file.journalist_username,
            password=sd_servers_with_submitted_file.journalist_password,
            otp_secret=sd_servers_with_submitted_file.journalist_otp_secret,
        )

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        # And the source has at least one submission
        initial_submissions_count = journ_app_nav.count_submissions_on_current_page()
        assert initial_submissions_count > 0

        # And the journalist selected the first submission
        journ_app_nav.journalist_selects_first_doc()

        # When the journalist clicks the delete button...
        journ_app_nav.journalist_clicks_delete_selected_link()
        # ...but then cancels the deletion
        journ_app_nav.nav_helper.safe_click_by_id("cancel-selected-deletions")

        # Then they see the same number of submissions as before
        submissions_after_canceling_count = journ_app_nav.count_submissions_on_current_page()
        assert submissions_after_canceling_count == initial_submissions_count

        # And when the journalist clicks the delete button...
        journ_app_nav.journalist_clicks_delete_selected_link()
        # ... and then confirms the deletion
        journ_app_nav.journalist_confirms_delete_selected()

        # Then they see less submissions than before because one was deleted
        def submission_deleted():
            submissions_after_confirming_count = journ_app_nav.count_submissions_on_current_page()
            assert submissions_after_confirming_count < initial_submissions_count

        journ_app_nav.nav_helper.wait_for(submission_deleted)

    def test_journalist_uses_col_delete_collection_button_modal(
        self, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_submitted_file.journalist_username,
            password=sd_servers_with_submitted_file.journalist_password,
            otp_secret=sd_servers_with_submitted_file.journalist_otp_secret,
        )

        # And the journalist went to the individual source's page
        journ_app_nav.journalist_visits_col()

        # And the source has at least one submission
        initial_submissions_count = journ_app_nav.count_submissions_on_current_page()
        assert initial_submissions_count > 0

        # When the journalist clicks the delete collection button...
        self._journalist_clicks_delete_collection_link(journ_app_nav)
        # ...but then cancels the deletion
        journ_app_nav.nav_helper.safe_click_by_id("cancel-collection-deletions")

        # Then they see the same number of submissions as before
        submissions_after_canceling_count = journ_app_nav.count_submissions_on_current_page()
        assert submissions_after_canceling_count == initial_submissions_count

        # When the journalist clicks the delete collection button...
        self._journalist_clicks_delete_collection_link(journ_app_nav)
        # ... and then confirms the deletion
        journ_app_nav.nav_helper.safe_click_by_id("delete-collection-button")

        # Then the journalist was redirected to the home page
        assert journ_app_nav.is_on_journalist_homepage()

    @staticmethod
    def _journalist_clicks_delete_collection_link(journ_app_nav: JournalistAppNavigator) -> None:
        journ_app_nav.nav_helper.safe_click_by_id("delete-collection-link")
        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_id("delete-collection-confirmation-modal")
        )

    def test_journalist_uses_index_delete_collections_button_modal(
        self, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_submitted_file.journalist_username,
            password=sd_servers_with_submitted_file.journalist_password,
            otp_secret=sd_servers_with_submitted_file.journalist_otp_secret,
        )

        # And at least one source previously used the app
        initial_sources_count = journ_app_nav.count_sources_on_index_page()
        assert initial_sources_count > 0

        # And the journalist selected all sources on the index page
        try:
            # If JavaScript is enabled, use the select_all button.
            journ_app_nav.driver.find_element_by_id("select_all")
            journ_app_nav.nav_helper.safe_click_by_id("select_all")
        except NoSuchElementException:
            journ_app_nav.nav_helper.safe_click_all_by_css_selector(
                'input[type="checkbox"][name="cols_selected"]'
            )

        # When the journalist clicks the delete collection button...
        self._journalist_clicks_delete_collections_link(journ_app_nav)
        # ...but then cancels the deletion
        self._journalist_clicks_delete_collections_cancel_on_first_modal(journ_app_nav)

        # Then they see the same number of sources as before
        assert initial_sources_count == journ_app_nav.count_sources_on_index_page()

        # And when the journalist clicks the delete collection button again...
        self._journalist_clicks_delete_collections_link(journ_app_nav)
        # ...and then confirms the deletion...
        self._journalist_clicks_delete_collections_on_first_modal(journ_app_nav)
        # ... and cancels the deletion on the second modal/confirmation prompt
        journ_app_nav.nav_helper.safe_click_by_id("cancel-collections-deletions")

        # Then they see the same number of sources as before
        assert initial_sources_count == journ_app_nav.count_sources_on_index_page()

        # And when the journalist clicks the delete collection button again and confirms it
        self._journalist_clicks_delete_collections_link(journ_app_nav)
        self._journalist_clicks_delete_collections_on_first_modal(journ_app_nav)
        journ_app_nav.nav_helper.safe_click_by_id("delete-collections-confirm")

        # Then a message shows up to say that the collection was deleted
        def collection_deleted():
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "The account and all data for the source have been deleted." in flash_msg.text

        journ_app_nav.nav_helper.wait_for(collection_deleted)

        # And the journalist gets redirected to the index with the source not present anymore
        def no_sources():
            assert journ_app_nav.count_sources_on_index_page() == 0

        journ_app_nav.nav_helper.wait_for(no_sources)

    @staticmethod
    def _journalist_clicks_delete_collections_link(journ_app_nav: JournalistAppNavigator) -> None:
        journ_app_nav.nav_helper.safe_click_by_id("delete-collections-link")
        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_id("delete-sources-modal")
        )

    @staticmethod
    def _journalist_clicks_delete_collections_cancel_on_first_modal(
        journ_app_nav: JournalistAppNavigator,
    ) -> None:
        journ_app_nav.nav_helper.safe_click_by_id("delete-menu-dialog-cancel")

    @staticmethod
    def _journalist_clicks_delete_collections_on_first_modal(
        journ_app_nav: JournalistAppNavigator,
    ) -> None:
        journ_app_nav.nav_helper.safe_click_by_id("delete-collections")
        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_id("delete-collections-confirm")
        )

    def test_journalist_interface_ui_with_modal(
        self, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_submitted_file.journalist_username,
            password=sd_servers_with_submitted_file.journalist_password,
            otp_secret=sd_servers_with_submitted_file.journalist_otp_secret,
        )

        # When the journalist uses the filter by sources to find text that doesn't match any source
        filter_box = journ_app_nav.nav_helper.safe_send_keys_by_id(
            "filter", "thiswordisnotinthewordlist"
        )

        # Then no sources are displayed on the page
        sources = journ_app_nav.get_sources_on_index_page()
        assert len(sources) > 0
        for source in sources:
            assert source.is_displayed() is False

        # And when the journalist clears the filter
        filter_box.clear()
        filter_box.send_keys(Keys.RETURN)

        # Then all sources are displayed
        for source in sources:
            assert source.is_displayed() is True

        # And given the journalist designation of the first source
        sources = journ_app_nav.get_sources_on_index_page()
        assert len(sources) > 0
        first_source_designation = sources[0].text

        # When the journalist uses the filter find this source designation
        filter_box.send_keys(first_source_designation)

        # Then only the corresponding source is displayed
        for source in sources:
            assert source.text == first_source_designation or source.is_displayed() is False

        # And when clicking "select all"
        select_all = journ_app_nav.driver.find_element_by_id("select_all")
        select_all.click()

        # Then only the visible source gets selected
        source_rows = journ_app_nav.driver.find_elements_by_css_selector("#cols li.source")
        for source_row in source_rows:
            source_designation = source_row.get_attribute("data-source-designation")
            checkbox = source_row.find_element_by_css_selector("input[type=checkbox]")
            if source_designation == first_source_designation:
                assert checkbox.is_selected()
            else:
                assert not checkbox.is_selected()

        # And when the journalist clears the filter and then selects all sources
        filter_box.clear()
        filter_box.send_keys(Keys.RETURN)
        select_all.click()
        for source_row in source_rows:
            checkbox = source_row.find_element_by_css_selector("input[type=checkbox]")
            assert checkbox.is_selected()

        # And then they filter again and click "select none"
        filter_box.send_keys(first_source_designation)
        select_none = journ_app_nav.driver.find_element_by_id("select_none")
        select_none.click()

        # Then only the visible source gets de-selected
        for source_row in source_rows:
            source_designation = source_row.get_attribute("data-source-designation")
            checkbox = source_row.find_element_by_css_selector("input[type=checkbox]")
            if source_designation == first_source_designation:
                assert not checkbox.is_selected()
            else:
                assert checkbox.is_selected()

        # And when the journalist clears the filter and leaves none selected
        filter_box.clear()
        filter_box.send_keys(Keys.RETURN)
        select_none.click()

        for source_row in source_rows:
            assert source_row.is_displayed()
            checkbox = source_row.find_element_by_css_selector("input[type=checkbox]")
            assert not checkbox.is_selected()

        # And the journalist clicks "select all" then all sources are selected
        journ_app_nav.driver.find_element_by_id("select_all").click()
        checkboxes = journ_app_nav.driver.find_elements_by_id("checkbox")
        for checkbox in checkboxes:
            assert checkbox.is_selected()

        # And when the journalist clicks "select none" then no sources are selected
        journ_app_nav.driver.find_element_by_id("select_none").click()
        checkboxes = journ_app_nav.driver.find_elements_by_id("checkbox")
        for checkbox in checkboxes:
            assert checkbox.is_selected() is False

        # And when the journalist clicks "select unread" then all unread sources are selected
        journ_app_nav.journalist_selects_the_first_source()
        journ_app_nav.driver.find_element_by_id("select_unread").click()
        checkboxes = journ_app_nav.get_submission_checkboxes_on_current_page()
        for checkbox in checkboxes:
            classes = checkbox.get_attribute("class")
            assert "unread-cb" in classes

        # And when the journalist clicks the delete button, it succeeds
        journ_app_nav.journalist_clicks_delete_all_and_sees_confirmation()

    def test_journalist_uses_index_delete_files_button_modal(
        self, sd_servers_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_with_submitted_file.journalist_username,
            password=sd_servers_with_submitted_file.journalist_password,
            otp_secret=sd_servers_with_submitted_file.journalist_otp_secret,
        )

        # And at least one source previously used the app
        initial_sources_count = journ_app_nav.count_sources_on_index_page()
        assert initial_sources_count > 0

        # And the journalist selected all sources on the index page
        try:
            # If JavaScript is enabled, use the select_all button.
            journ_app_nav.driver.find_element_by_id("select_all")
            journ_app_nav.nav_helper.safe_click_by_id("select_all")
        except NoSuchElementException:
            journ_app_nav.nav_helper.safe_click_all_by_css_selector(
                'input[type="checkbox"][name="cols_selected"]'
            )

        # When the journalist clicks the delete collection button...
        self._journalist_clicks_delete_collections_link(journ_app_nav)
        # ...and then clicks the delete files button on the first modal
        journ_app_nav.nav_helper.safe_click_by_id("delete-files-and-messages")

        # Then they are redirected to the index with the source present, files
        # and messages zeroed, and a success flash message present
        def one_source_no_files():
            assert journ_app_nav.count_sources_on_index_page() == 1
            flash_msg = journ_app_nav.driver.find_element_by_css_selector(".flash")
            assert "The files and messages have been deleted" in flash_msg.text
            counts = journ_app_nav.driver.find_elements_by_css_selector(".submission-count")
            assert "0 docs" in counts[0].text
            assert "0 messages" in counts[1].text

        journ_app_nav.nav_helper.wait_for(one_source_no_files)


@pytest.fixture(scope="function")
def _sd_servers_with_missing_file(
    setup_journalist_key_and_gpg_folder: Tuple[str, Path]
) -> Generator[SdServersFixtureResult, None, None]:
    """Same as sd_servers but spawns the apps with a submission whose file has been deleted."""
    default_config = SecureDropConfigFactory.create(
        SECUREDROP_DATA_ROOT=Path(f"/tmp/sd-tests/functional-with-missing-file-{uuid4()}"),
    )

    # Ensure the GPG settings match the one in the config to use, to ensure consistency
    journalist_key_fingerprint, gpg_dir = setup_journalist_key_and_gpg_folder
    assert Path(default_config.GPG_KEY_DIR) == gpg_dir
    assert default_config.JOURNALIST_KEY == journalist_key_fingerprint

    # Spawn the apps in separate processes with a callback have a submission with a missing file
    with spawn_sd_servers(
        config_to_use=default_config,
        journalist_app_setup_callback=_create_submission_with_missing_file,
    ) as sd_servers_result:
        yield sd_servers_result


def _create_submission_with_missing_file(config_in_use: SecureDropConfig) -> None:
    _, submission_file_path = create_source_and_submission(config_in_use)
    submission_file_path.unlink()


class TestJournalistMissingFile:
    """Test error handling when a message file has been deleted from disk but remains in the
    database. Ref #4787."""

    def test_download_source_unread(self, _sd_servers_with_missing_file, firefox_web_driver):
        # Given an SD server with a submission whose file was deleted from disk
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=_sd_servers_with_missing_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=_sd_servers_with_missing_file.journalist_username,
            password=_sd_servers_with_missing_file.journalist_password,
            otp_secret=_sd_servers_with_missing_file.journalist_otp_secret,
        )

        # When the journalist clicks on the source's "n unread" button
        journ_app_nav.driver.find_element_by_css_selector(
            "table#collections tr.source > td.unread a"
        ).click()

        # Then they see the expected error message
        self._journalist_sees_missing_file_error_message(journ_app_nav)
        journ_app_nav.is_on_journalist_homepage()

    @staticmethod
    def _journalist_sees_missing_file_error_message(journ_app_nav: JournalistAppNavigator) -> None:
        notification = journ_app_nav.driver.find_element_by_css_selector(".error")

        # We use a definite article ("the" instead of "a") if a single file
        # is downloaded directly.
        error_msg = (
            "Your download failed because the file could not be found. An admin can find "
            + "more information in the system and monitoring logs."
        )

        assert notification.text in error_msg

    def test_select_source_and_download_all(
        self, _sd_servers_with_missing_file, firefox_web_driver
    ):
        # Given an SD server with a submission whose file was deleted from disk
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=_sd_servers_with_missing_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=_sd_servers_with_missing_file.journalist_username,
            password=_sd_servers_with_missing_file.journalist_password,
            otp_secret=_sd_servers_with_missing_file.journalist_otp_secret,
        )

        # When the journalist selects the source and then clicks the "Download" button
        checkboxes = journ_app_nav.driver.find_elements_by_name("cols_selected")
        assert len(checkboxes) == 1
        checkboxes[0].click()
        journ_app_nav.driver.find_element_by_xpath("//button[@value='download-all']").click()

        # Then they see the expected error message
        self._journalist_sees_missing_file_error_message(journ_app_nav)
        journ_app_nav.is_on_journalist_homepage()

    def test_select_source_and_download_unread(
        self, _sd_servers_with_missing_file, firefox_web_driver
    ):
        # Given an SD server with a submission whose file was deleted from disk
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=_sd_servers_with_missing_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=_sd_servers_with_missing_file.journalist_username,
            password=_sd_servers_with_missing_file.journalist_password,
            otp_secret=_sd_servers_with_missing_file.journalist_otp_secret,
        )

        # When the journalist selects the source then clicks the "Download Unread" button
        checkboxes = journ_app_nav.driver.find_elements_by_name("cols_selected")
        assert len(checkboxes) == 1
        checkboxes[0].click()
        journ_app_nav.driver.find_element_by_xpath("//button[@value='download-unread']").click()

        # Then they see the expected error message
        self._journalist_sees_missing_file_error_message(journ_app_nav)
        journ_app_nav.is_on_journalist_homepage()

    def test_download_message(self, _sd_servers_with_missing_file, firefox_web_driver):
        # Given an SD server with a submission whose file was deleted from disk
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=_sd_servers_with_missing_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=_sd_servers_with_missing_file.journalist_username,
            password=_sd_servers_with_missing_file.journalist_password,
            otp_secret=_sd_servers_with_missing_file.journalist_otp_secret,
        )

        # When the journalist clicks on the individual message from the source page
        journ_app_nav.journalist_checks_messages()
        journ_app_nav.journalist_selects_the_first_source()

        journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_css_selector("table#submissions")
        )
        submissions = journ_app_nav.driver.find_elements_by_css_selector("#submissions a")
        assert 1 == len(submissions)

        file_link = submissions[0]
        file_link.click()

        # Then they see the expected error message
        self._journalist_sees_missing_file_error_message(journ_app_nav)
        self._journalist_is_on_collection_page(journ_app_nav)

    @staticmethod
    def _journalist_is_on_collection_page(journ_app_nav: JournalistAppNavigator) -> None:
        return journ_app_nav.nav_helper.wait_for(
            lambda: journ_app_nav.driver.find_element_by_css_selector("div.journalist-view-single")
        )

    def test_select_message_and_download_selected(
        self, _sd_servers_with_missing_file, firefox_web_driver
    ):
        # Given an SD server with a submission whose file was deleted from disk
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=_sd_servers_with_missing_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=_sd_servers_with_missing_file.journalist_username,
            password=_sd_servers_with_missing_file.journalist_password,
            otp_secret=_sd_servers_with_missing_file.journalist_otp_secret,
        )
        # When the journalist selects the individual message from the source page
        # and clicks "Download Selected"
        journ_app_nav.journalist_selects_the_first_source()
        checkboxes = journ_app_nav.driver.find_elements_by_name("doc_names_selected")
        assert len(checkboxes) == 1
        checkboxes[0].click()
        journ_app_nav.driver.find_element_by_xpath("//button[@value='download']").click()

        # Then they see the expected error message
        self._journalist_sees_missing_file_error_message(journ_app_nav)
        self._journalist_is_on_collection_page(journ_app_nav)
