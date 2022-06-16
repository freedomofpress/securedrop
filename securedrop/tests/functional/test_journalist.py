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

import pytest

from source_user import _SourceScryptManager
from tests.functional import functional_test as ft
from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
from store import Storage

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from tests.functional.app_navigators import JournalistAppNavigator


class TestJournalist:
    def test_journalist_verifies_deletion_of_one_submission_modal(
        self, sd_servers_v2_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2_with_submitted_file.journalist_username,
            password=sd_servers_v2_with_submitted_file.journalist_password,
            otp_secret=sd_servers_v2_with_submitted_file.journalist_otp_secret,
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
        journ_app_nav.nav_helper.safe_click_by_id("delete-selected")

        # Then they see less submissions than before because one was deleted
        def submission_deleted():
            submissions_after_confirming_count = journ_app_nav.count_submissions_on_current_page()
            assert submissions_after_confirming_count < initial_submissions_count

        journ_app_nav.nav_helper.wait_for(submission_deleted)

    def test_journalist_uses_col_delete_collection_button_modal(
        self, sd_servers_v2_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2_with_submitted_file.journalist_username,
            password=sd_servers_v2_with_submitted_file.journalist_password,
            otp_secret=sd_servers_v2_with_submitted_file.journalist_otp_secret,
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
        self, sd_servers_v2_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2_with_submitted_file.journalist_username,
            password=sd_servers_v2_with_submitted_file.journalist_password,
            otp_secret=sd_servers_v2_with_submitted_file.journalist_otp_secret,
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
        self, sd_servers_v2_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2_with_submitted_file.journalist_username,
            password=sd_servers_v2_with_submitted_file.journalist_password,
            otp_secret=sd_servers_v2_with_submitted_file.journalist_otp_secret,
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
        journ_app_nav.nav_helper.safe_click_all_by_css_selector("[name=doc_names_selected]")
        journ_app_nav.nav_helper.safe_click_by_css_selector("a#delete-selected-link")

    def test_journalist_uses_index_delete_files_button_modal(
        self, sd_servers_v2_with_submitted_file, firefox_web_driver
    ):
        # Given an SD server with a file submitted by a source
        # And a journalist logged into the journalist interface
        journ_app_nav = JournalistAppNavigator(
            journalist_app_base_url=sd_servers_v2_with_submitted_file.journalist_app_base_url,
            web_driver=firefox_web_driver,
        )
        journ_app_nav.journalist_logs_in(
            username=sd_servers_v2_with_submitted_file.journalist_username,
            password=sd_servers_v2_with_submitted_file.journalist_password,
            otp_secret=sd_servers_v2_with_submitted_file.journalist_otp_secret,
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


class TestJournalistMissingFile(
    ft.FunctionalTest,
    source_navigation_steps.SourceNavigationStepsMixin,
    journalist_navigation_steps.JournalistNavigationStepsMixin
):
    """Test error handling when a message file has been deleted from disk but remains in the
    database. Ref #4787."""

    @pytest.fixture(scope="function")
    def missing_msg_file(self):
        """Fixture to setup the message with missing file used in the following tests."""
        # Submit a message
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._source_logs_out()

        # Remove the message file from the store
        filesystem_id = _SourceScryptManager.get_default().derive_source_filesystem_id(
            self.source_name
        )
        storage_path = Path(Storage.get_default().storage_path) / filesystem_id
        msg_files = [p for p in storage_path.glob("*-msg.gpg")]
        assert len(msg_files) == 1
        msg_files[0].unlink()

        self.switch_to_firefox_driver()

        yield

        self.switch_to_torbrowser_driver()

    def test_download_source_unread(self, missing_msg_file):
        """Test behavior when the journalist clicks on the source's "n unread" button from the
        journalist home page."""
        self._journalist_logs_in()
        self._journalist_clicks_source_unread()
        self._journalist_sees_missing_file_error_message(single_file=True)
        self._is_on_journalist_homepage()

    def test_select_source_and_download_all(self, missing_msg_file):
        """Test behavior when the journalist selects the source then clicks the "Download" button
        from the journalist home page."""
        self._journalist_logs_in()
        self._journalist_selects_first_source_then_download_all()
        self._journalist_sees_missing_file_error_message(single_file=True)
        self._is_on_journalist_homepage()

    def test_select_source_and_download_unread(self, missing_msg_file):
        """Test behavior when the journalist selects the source then clicks the "Download Unread"
        button from the journalist home page."""
        self._journalist_logs_in()
        self._journalist_selects_first_source_then_download_unread()
        self._journalist_sees_missing_file_error_message(single_file=True)
        self._is_on_journalist_homepage()

    def test_download_message(self, missing_msg_file):
        """Test behavior when the journalist clicks on the individual message from the source page.
        """
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message_missing_file()
        self._journalist_sees_missing_file_error_message(single_file=True)
        self._journalist_is_on_collection_page()

    def test_select_message_and_download_selected(self, missing_msg_file):
        """Test behavior when the journalist selects the individual message from the source page
        then clicks "Download Selected"."""
        self._journalist_logs_in()
        self._journalist_selects_the_first_source()
        self._journalist_selects_message_then_download_selected()
        self._journalist_sees_missing_file_error_message(single_file=True)
        self._journalist_is_on_collection_page()
