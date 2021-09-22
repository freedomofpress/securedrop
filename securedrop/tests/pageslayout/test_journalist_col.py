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
import pytest

from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
import tests.pageslayout.functional_test as pft


@pytest.mark.pagelayout
class TestJournalistLayoutCol(
        pft.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_col_no_documents(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._journalist_delete_all()
        self._journalist_confirm_delete_selected()
        self._screenshot('journalist-col_no_document.png')
        self._save_html('journalist-col_no_document.html')

    def test_col_has_no_key(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._source_delete_key()
        self._journalist_visits_col()
        self._screenshot('journalist-col_has_no_key.png')
        self._save_html('journalist-col_has_no_key.html')

    def test_col(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._screenshot('journalist-col.png')
        self._save_html('journalist-col.html')

    def test_col_javascript(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_visits_col()
        self._screenshot('journalist-col_javascript.png')
        self._save_html('journalist-col_javascript.html')
