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
from . import functional_test
import pytest


@pytest.mark.pagelayout
class TestSourceLayout(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_lookup(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._screenshot('source-lookup.png')
        self._save_html('source-lookup.html')

    def test_lookup_shows_codename(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message(first_submission=True)
        self._source_shows_codename()
        self._screenshot('source-lookup-shows-codename.png')
        self._save_html('source-lookup-shows-codename.html')

    def test_login(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._screenshot('source-login.png')
        self._save_html('source-login.html')

    def test_enters_text_in_login_form(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_enters_codename_in_login_form()
        self._screenshot('source-enter-codename-in-login.png')
        self._save_html('source-enter-codename-in-login.html')

    def test_generate(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._screenshot('source-generate.png')
        self._save_html('source-generate.html')

    def test_submission_entered_text(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_enters_text_in_message_field()
        self._screenshot('source-submission_entered_text.png')
        self._save_html('source-submission_entered_text.html')

    def test_next_submission_flashed_message(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._screenshot('source-next_submission_flashed_message.png')
        self._save_html('source-next_submission_flashed_message.html')

    def test_source_checks_for_reply(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file(first_submission=True)
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
        self._journalist_sends_reply_to_source()
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_proceeds_to_login()
        self._screenshot('source-checks_for_reply.png')
        self._save_html('source-checks_for_reply.html')
        self._source_deletes_a_journalist_reply()
        self._screenshot('source-deletes_reply.png')
        self._save_html('source-deletes_reply.html')
