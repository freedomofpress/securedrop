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
class TestJournalistLayout(
        pft.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_login(self):
        self.driver.get(self.journalist_location + "/login")
        self._screenshot('journalist-login.png')
        self._save_html('journalist-login.html')

    def test_journalist_composes_reply(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_logs_out()
        self._journalist_logs_in()
        self._journalist_checks_messages()
        self._journalist_downloads_message()
        self._journalist_composes_reply()
        self._screenshot('journalist-composes_reply.png')
        self._save_html('journalist-composes_reply.html')

    def test_edit_account_user(self):
        self._journalist_logs_in()
        self._visit_edit_account()
        self._screenshot('journalist-edit_account_user.png')
        self._save_html('journalist-edit_account_user.html')

    def test_index_no_documents_admin(self):
        self._admin_logs_in()
        self._screenshot('journalist-admin_index_no_documents.png')
        self._save_html('journalist-admin_index_no_documents.html')

    def test_index_no_documents(self):
        self._journalist_logs_in()
        self._screenshot('journalist-index_no_documents.png')
        self._save_html('journalist-index_no_documents.html')

    def test_index(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._screenshot('journalist-index.png')
        self._save_html('journalist-index.html')

    def test_index_javascript(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()
        self._source_submits_a_message()
        self._source_logs_out()
        self._journalist_logs_in()
        self._screenshot('journalist-index_javascript.png')
        self._save_html('journalist-index_javascript.html')
        self._journalist_selects_the_first_source()
        self._journalist_selects_all_documents()
        self._screenshot(
            'journalist-clicks_on_source_and_selects_documents.png'
        )
        self._save_html(
            'journalist-clicks_on_source_and_selects_documents.html'
        )

    def test_index_entered_text(self):
        self._input_text_in_login_form('jane_doe', 'my password is long',
                                       '117264')
        self._screenshot('journalist-index_with_text.png')
        self._save_html('journalist-index_with_text.html')

    def test_fail_to_visit_admin(self):
        self._journalist_visits_admin()
        self._screenshot('journalist-code-fail_to_visit_admin.png')
        self._save_html('journalist-code-fail_to_visit_admin.html')

    def test_fail_login(self, hardening):
        self._journalist_fail_login()
        self._screenshot('journalist-code-fail_login.png')
        self._save_html('journalist-code-fail_login.html')

    def test_fail_login_many(self, hardening):
        self._journalist_fail_login_many()
        self._screenshot('journalist-code-fail_login_many.png')
        self._save_html('journalist-code-fail_login_many.html')
