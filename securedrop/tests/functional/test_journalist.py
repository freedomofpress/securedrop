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
from . import functional_test as ft
from . import journalist_navigation_steps
from . import source_navigation_steps
from store import Storage

from tbselenium.utils import SECURITY_LOW


class TestJournalist(
    ft.FunctionalTest,
    source_navigation_steps.SourceNavigationStepsMixin,
    journalist_navigation_steps.JournalistNavigationStepsMixin,
):
    def test_journalist_verifies_deletion_of_one_submission_modal(self):
        # This deletion button is displayed on the individual source page
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_uses_delete_selected_button_confirmation()

    def test_journalist_uses_col_delete_collection_button_modal(self):
        # This delete button is displayed on the individual source page
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_uses_delete_collection_button_confirmation()

    def test_journalist_uses_index_delete_collections_button_modal(self):
        # This deletion button is displayed on the index page
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_uses_delete_collections_button_confirmation()

    def test_journalist_uses_index_delete_files_button_modal(self):
        # This deletion button is displayed on the index page
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_uses_index_delete_files_button_confirmation()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()
        self._source_logs_out()

    def test_journalist_interface_ui_with_modal(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()

        self.set_tbb_securitylevel(SECURITY_LOW)

        self._journalist_logs_in()
        self._journalist_uses_js_filter_by_sources()
        self._journalist_source_selection_honors_filter()
        self._journalist_selects_all_sources_then_selects_none()
        self._journalist_selects_the_first_source()
        self._journalist_uses_js_buttons_to_download_unread()
        self._journalist_delete_all_confirmation()


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
