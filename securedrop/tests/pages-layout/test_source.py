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
from tests.functional import journalist_navigation_steps
from tests.functional import source_navigation_steps
import functional_test


class TestSourceLayout(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationSteps,
        journalist_navigation_steps.JournalistNavigationSteps):

    def test_index(self):
        self._source_visits_source_homepage()
        self._screenshot('source-index.png')

    def test_index_javascript(self):
        self._javascript_toggle()
        self._source_visits_source_homepage()
        self._screenshot('source-index_javascript.png')

    def test_lookup(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._screenshot('source-lookup.png')

    def test_login(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._screenshot('source-login.png')

    def test_use_tor_browser(self):
        self._source_visits_use_tor()
        self._screenshot('source-use_tor_browser.png')

    def test_generate(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._screenshot('source-generate.png')
