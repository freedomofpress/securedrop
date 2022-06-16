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
from tests.functional.functional_test import TORBROWSER
from . import functional_test


@pytest.mark.pagelayout
class TestSourceLayoutTorbrowser(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):
    default_driver_name = TORBROWSER

    def test_index(self):
        self.disable_js_torbrowser_driver()
        self._source_visits_source_homepage()
        self._screenshot('source-index.png')
        self._save_html('source-index.html')

    def test_logout(self):
        self.disable_js_torbrowser_driver()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._screenshot('source-logout_page.png')
        self._save_html('source-logout_page.html')
