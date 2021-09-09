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
import time

import pytest

from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
import tests.pageslayout.functional_test as pft


@pytest.mark.pagelayout
class TestJournalistLayoutDelete(
        pft.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_delete_none(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_clicks_delete_selected_link()
        self._journalist_confirm_delete_selected()
        self._screenshot('journalist-delete_none.png')
        self._save_html('journalist-delete_none.html')

    def test_delete_one_confirmation(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_selects_first_doc()
        self._journalist_clicks_delete_selected_link()
        time.sleep(1)
        self._screenshot('journalist-delete_one_confirmation.png')
        self._save_html('journalist-delete_one_confirmation.html')

    def test_delete_all_confirmation(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all_confirmation()
        time.sleep(1)
        self._screenshot('journalist-delete_all_confirmation.png')
        self._save_html('journalist-delete_all_confirmation.html')

    def test_delete_one(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_one()
        self._journalist_confirm_delete_selected()
        self._screenshot('journalist-delete_one.png')
        self._save_html('journalist-delete_one.html')

    def test_delete_all(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all()
        self._journalist_confirm_delete_selected()
        self._screenshot('journalist-delete_all.png')
        self._save_html('journalist-delete_all.html')
