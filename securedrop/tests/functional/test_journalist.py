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

from . import functional_test as ft
from . import journalist_navigation_steps
from . import source_navigation_steps


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

    def test_journalist_interface_ui_with_modal(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()

        # Toggle security slider to force prefs change
        self.set_tbb_securitylevel(ft.TBB_SECURITY_HIGH)
        self.set_tbb_securitylevel(ft.TBB_SECURITY_LOW)

        self._journalist_logs_in()
        self._journalist_uses_js_filter_by_sources()
        self._journalist_source_selection_honors_filter()
        self._journalist_selects_all_sources_then_selects_none()
        self._journalist_selects_the_first_source()
        self._journalist_uses_js_buttons_to_download_unread()
        self._journalist_delete_all_confirmation()
