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
from tests.functional.functional_test import TORBROWSER
from . import functional_test
import pytest


@pytest.mark.pagelayout
class TestSourceSessionLayout(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):
    default_driver_name = TORBROWSER

    session_expiration = 5

    def test_source_session_timeout(self):
        self.disable_js_torbrowser_driver()
        self._source_visits_source_homepage()
        self._source_clicks_submit_documents_on_homepage()
        self._source_continues_to_submit_page()
        self._source_waits_for_session_to_timeout()
        self._source_enters_text_in_message_field()
        self._source_visits_source_homepage()
        self._screenshot('source-session_timeout.png')
        self._save_html('source-session_timeout.html')
